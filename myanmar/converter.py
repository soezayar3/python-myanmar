#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""self module contains functions for conversion between unicode and Myanmar legacy
encodings.

To get the 
>>> dbfile = read(open('test.dat', 'r'))

To split a number:

>>> dbfile.split('01006')
['0', '100', '6']
>>> dbfile.split('902006')
['90', '20', '06']
>>> dbfile.split('909856')
['90', '985', '6']

To split the number and get properties for each part:

>>> dbfile.info('01006')

"""
import json
import re

class TlsMyanmarConverter ():

    def __init__ (self, data):
        self.data = data
        self.useZwsp = False
        self.sourceEncoding = self.data['fonts'][0]
        self.unicodeSequence = ["kinzi",None,"lig",None,"cons","stack",
                                "asat","yapin","yayit", "wasway","hatoh",
                                "eVowel","uVowel","lVowel","anusvara",
                                "aVowel","lDot","asat","lDot","visarga"]
        self.legacySequence  =  ["eVowel","yayit",None,"lig",None,"cons","stack",
                                 "kinzi", "uVowel","anusvara","asat","stack","yapin",
                                 "wasway","hatoh","wasway","yapin","kinzi", "uVowel",
                                 "lDot","lVowel","lDot","anusvara","uVowel","lVowel",
                                 "aVowel","stack", "lDot","visarga","asat","lDot",
                                 "visarga","lDot"]
        self.minCodePoint = None
        self.reverse = {}
        self.unicodePattern = self.buildRegExp(self.unicodeSequence, True)
        self.legacyPattern  = self.buildRegExp(self.legacySequence, False)
        self.fontFamily = ""
        i = 0
        for font in self.data['fonts']:
            if (i > 0):
                self.fontFamily += ","
            self.fontFamily += "'" + font + "'"
            i = i + 1

    def buildRegExp (self, sequence, isUnicode):
        pattern = u""
        escapeRe = re.compile (ur"([\^\$\\\.\*\+\?\(\)\[\]\{\}\|])", re.UNICODE) 
        if not self.reverse:
            self.reverse = {}

        if self.minCodePoint == None:
            self.minCodePoint = ord(self.data["cons"][u"\u1000"][0])
            self.maxCodePoint = self.minCodePoint

        for i in range(0, len(sequence)):
            alternates = []
            if sequence[i] is None:
                continue
            if not self.reverse.has_key(sequence[i]):
                self.reverse[sequence[i]] = {} #new Object()
                #print self.maxCodePoint, self.minCodePoint
            for j in self.data[sequence[i]]:
                #print 'j =  ', j.encode ('utf-8')
                if self.data[sequence[i]][j] and len(self.data[sequence[i]][j]) > 0: 
                    for k in range(0, len(self.data[sequence[i]][j])):
                        codePoint = ord(self.data[sequence[i]][j][k])
                        if codePoint != 0x20:
                            if (codePoint > self.maxCodePoint):
                                self.maxCodePoint = codePoint
                            if (codePoint < self.minCodePoint):
                                self.minCodePoint = codePoint
                #print self.data[sequence[i]][j].encode ('utf-8')
                if (isUnicode):
                    #items with an underscore suffix are not put into the regexp
                    #but they are used to build the legacy to unicode map
                    underscore = j.find('_')
                    if (underscore == -1):
                        self.reverse[sequence[i]][self.data[sequence[i]][j]] = j
                        #FIXME:
                        #print 'j =  ', j.encode ('utf-8') , ' escapes= ', escapeRe.sub (ur"\1", j).encode ('utf-8')
                        alternates += [escapeRe.sub (ur"\1", j)]
                    else:
                        self.reverse[sequence[i]][self.data[sequence[i]][j]] = j[0:underscore]
                else:
                    #FIXME
                    #print self.data[sequence[i]][j].encode ('utf-8')
                    #print 'j =  ', j.encode ('utf-8') , ' escapes= ', escapeRe.sub (ur"\1", j).encode ('utf-8')
                    escapedAlternate = escapeRe.sub (ur"\1", self.data[sequence[i]][j])
                    if escapedAlternate:
                        alternates += [escapedAlternate]

            alternates.sort(self.sortLongestFirst)
            #print alternates
            if (sequence[i] == "cons"):
                pattern += "("
            elif (sequence[i] == "lig"):
                pattern += "("
            pattern += "("
            subPattern = ""

            #print "alternates .... = ", alternates
            if alternates is not None:
                first = True
                for k in alternates:
                    if first:
                        subPattern = subPattern + k
                        first = False
                    else:
                        subPattern = subPattern + "|" + k
            if sequence[i] == "stack":
                self.legacyStackPattern = re.compile (subPattern, re.UNICODE)
            if (sequence[i] == "kinzi"):
                self.legacyKinziPattern = re.compile (subPattern, re.UNICODE)
            if (sequence[i] == "lig"):
                self.legacyLigPattern = re.compile (subPattern, re.UNICODE)

            pattern += subPattern + ")"
            
            if (sequence[i] == "cons"):
                pass
            elif (sequence[i] == "lig"):
                pattern += "|"
            elif (sequence[i] == "stack" and sequence[i-1] == "cons"):
                pattern += "?))"
            elif (sequence[i] == "wasway" or sequence[i] == "hatoh" or
                  sequence[i] == "uVowel" or sequence[i] == "lVowel" or sequence[i] == "aVowel" or
                  sequence[i] == "lDot" or sequence[i] == "visarga"):
                if (isUnicode):
                    pattern += "?"
                else:
                    pattern += "*" #these are frequently multi-typed
            else:
                pattern += "?"

        #print pattern
        return re.compile(pattern, re.UNICODE)

    def sortLongestFirst (self, a,b):
        #print a.encode ('utf-8'), b.encode ('utf-8')
        if len(a) > len(b):
            return -1;
        elif len(a) <len (b):
            return 1;
        elif (a < b):
            return -1;
        elif (a > b):
            return 1;
        return 0; 

    def convertToUnicodeSyllables (self, inputText):
        outputText = u""
        syllables = []
        pos = 0
        prevSyllable = None
        for match in self.legacyPattern.finditer(inputText):
            if (match.start() != pos):
                prevSyllable = None
                nonMatched = inputText[pos:match.pos]
                outputText += nonMatched
                syllables += nonMatched 
            prevSyllable = self.toUnicodeMapper(inputText, match.group(), prevSyllable)
            syllables += prevSyllable
            outputText += prevSyllable
            pos = match.end ()

        if (pos < len(inputText)):
            nonMatched = inputText[pos:len(inputText)]
            #print type(nonMatched), type(outputText)
            outputText += nonMatched
            syllables += nonMatched 
    
        ret = {}
        ret['outputText'] = outputText
        ret['syllables'] = syllables
        return ret

    def toUnicodeMapper (self, inputText, matchData, prevSyllable):
        syllable = {}

        for match in matchData:
            for component in self.legacySequence:
                if component == None:
                    continue

                if self.reverse[component].has_key(match):
                    syllable[component] = self.reverse[component][match]
                else:
                    continue
                
                # check a few sequences putting ligature components in right place
                if (len(syllable[component]) > 1):
                    if (component == "yapin"):
                        if (syllable[component][1] == u"ွ"):
                            syllable["wasway"] = u"ွ"
                            if (len(syllable[component]) > 2):
                                if (syllable[component][2] == u"ှ"):
                                    syllable["hatoh"] = u"ှ"
                                #else:
                                    #self.debug.print("Unhandled yapin ligature: " + syllable[component])
                                syllable[component] = syllable[component][0:1]
                        elif (syllable[component][1] == u"ှ"or len(syllable[componen]) > 2):
                            syllable["hatoh"] = u"ှ"
                            syllable[component] = syllable[component][0:1]
                    elif (component == "yayit"):
                        if (syllable[component][1] == u"ွ"):
                            syllable["wasway"] = u"ွ"
                        elif (syllable[component][1] == u"ု"):
                            syllable["lVowel"] = u"ု"
                        elif (syllable[component][1] == u"ိ" and
                              len(syllable[component]) > 2 and
                              syllable[component][2] == u"ု"):
                            syllable["uVowel"] = u"ိ"
                            syllable["lVowel"] = u"ု"                
    #                    else:
    #                        self.debug.print("unhandled yayit ligature: " + syllable[component])
                        syllable[component] = syllable[component][0:1]
                    elif (component == "wasway"):
                        syllable["hatoh"] = syllable[component][1:2]
                        syllable[component] = syllable[component][0:1]
                    elif (component == "hatoh"):
                        syllable["lVowel"] = syllable[component][1:2]
                        syllable[component] = syllable[component][0:1]
                    elif (component == "uVowel"):
                        syllable["anusvara"] = syllable[component][1:2]
                        syllable[component] = syllable[component][0:1]
                    elif (component == "aVowel"):
                        syllable["asat"] = syllable[component][1:2]
                        syllable[component] = syllable[component][0:1]
                    elif (component == "kinzi"):
                        # kinzi is length 3 to start with
                        if ((len(syllable[component]) > 3 and syllable[component][3] == u"ံ" )or
                            (len(syllable[component]) > 4 and syllable[component][4] == u"ံ")):
                                  syllable["anusvara"] = u"ံ"
                        if (len(syllable[component]) > 3 and
                            (syllable[component][3] == u"ိ" or syllable[component][3] == u"ီ")):
                            syllable["uVowel"] = syllable[component][3]
                        syllable[component] = syllable[component][0:3]
                    elif (component == "cons"):
                        if (syllable[component][1] == u"ာ"):
                            syllable["aVowel"] = syllable[component][1]
                            syllable[component] = syllable[component][0:1]
                    elif (component == "stack" or component == "lig"):
                        # should be safe to ignore, since the relative order is correct
                        pass
                    #else:
                    #   self.debug.print("unhandled ligature: " + component + " " + syllable[component])

        # now some post processing
        if (syllable.has_key("asat")):
            if ( not syllable.has_key("eVowel") and
                 (syllable.has_key ("yayit") or
                  syllable.has_key ("yapin") or
                  syllable.has_key ("wasway") or
                  syllable.has_key ("lVowel"))):
                syllable["contraction"] = syllable["asat"]
                del syllable["asat"]
            if (syllable.has_key ("cons") and syllable["cons"] == u"ဥ"):
                syllable["cons"] = u"ဉ"
                    
        if (syllable.has_key ("cons") and syllable["cons"] == u"ဥ" and syllable.has_key("uVowel")):
            syllable["cons"] = u"ဦ"
            if syllable.has_key ("uVowel"):
                del syllable["uVowel"]

        elif (syllable.has_key ("cons") and syllable["cons"] == u"စ" and syllable.has_key("yapin")):
            syllable["cons"] = u"ဈ"
            if syllable.has_key ("yapin"):
                del syllable["yapin"]

        elif (syllable.has_key ("cons") and syllable["cons"] == u"သ" and syllable.has_key("yayit")):
            if (syllable.has_key("eVowel") and
                syllable.has_key ("aVowel") and
                syllable.has_key ("asat")):
                syllable["cons"] = u"ဪ"
                if syllable.has_key ("yayit"):
                    del syllable["yayit"]
                if syllable.has_key ("eVowel"):
                    del syllable["eVowel"]
                if syllable.has_key ("aVowel"):
                    del syllable["aVowel"]
                if syllable.has_key ("asat"):
                    del syllable["asat"]
            else:
                syllable["cons"] = u"ဩ"
                if syllable.has_key ("yayit"):
                    del syllable["yayit"]

        elif (syllable.has_key ("cons") and syllable["cons"] == u"၀"):
            index  = matchData.find (u'၀')
            def is_mynum (c):
                return (c >= u'၁' and c <= u'၉')
            if (index-1 > 0 and not is_mynum(matchData[index-1])):
                syllable["cons"] == u'ဝ'
            if (index+1 < len(matchData) and not is_mynum(matchData[index+1])):
                syllable["cons"] = u'ဝ'
                
        elif (syllable.has_key ("cons") and syllable["cons"] == u"၄" and
              matchData.find (u'င်း') != matchData.find (u'၄') + 1):
            syllable["cons"] = u'၎'

        elif (syllable.has_key ("cons") and syllable["cons"] == u'၇' and
              (syllable.has_key("eVowel") or syllable.has_key("uVowel") or
               syllable.has_key("lVowel") or syllable.has_key("anusvara") or 
               syllable.has_key("aVowel") or syllable.has_key("lDot") or
               syllable.has_key("asat") or syllable.has_key("wasway") or
               syllable.has_key("hatoh"))):
            syllable ["cons"] = u'ရ'

        outputOrder = ["kinzi","lig","cons","numbers","stack",
                       "contraction","yapin","yayit", "wasway",
                       "hatoh","eVowel","uVowel","lVowel","anusvara",
                       "aVowel","lDot","asat","visarga"]

        outputText = ""
        if (self.useZwsp and not syllable["kinzi"] and not syllable["lig"]
            and not syllable["stack"] and not syllable["contraction"]
            and not syllable["asat"] and (prevSyllable != u"အ") and (prevSyllable != None)):
            outputText += u"\u200B"
        
        for output in outputOrder:
            if syllable.has_key(output):
                outputText += "".join(syllable[output])

        return outputText
    
    def convertToUnicode (self, inputText):
        return self.convertToUnicodeSyllables (inputText)['outputText']

    # def convertFromUnicode (self, inputText):
    #     inputText = re.sub (ur'\u200B\u2060', '', inputText);
    #     outputText = u""
    #     pos = 0
    #     for match in self.unicodePattern.finditer (inputText):
    #         outputText += inputText[pos:match.start()]
    #         pos = match.end ()
    #         outputText += self.fromUnicodeMapper(inputText, match.group())

    #     if (pos < len(inputText)):
    #         outputText += inputText[pos:len(inputText)]
    #     return outputText

    # def fromUnicodeMapper (self, inputText, matchData):
    #     #TODO 
    #     unicodeSyllable = {}
    #     syllable = {}

    #     for match in matchData:
    #         for component in self.unicodeSequence:
    #             if (component == None):
    #                 continue
    #             unicodeSyllable[component] = match
    #             syllable[component] = self.data[component][match]

    #     if (unicodeSyllable.has_key ("kinzi")):
    #         if (unicodeSyllable.has_key ("uVowel")):
    #             if (unicodeSyllable.has_key ("anusvara")):
    #                 key = unicodeSyllable["anusvara"] + unicodeSyllable["uVowel"] + unicodeSyllable["anusvara"] + "_lig"
    #                 if (self.data["kinzi"][key] and len(self.data["kinzi"][key])):
    #                     syllable["kinzi"] = self.data["kinzi"][key]
    #                     del syllable["anusvara"]
    #             else:
    #                 key = unicodeSyllable["kinzi"] + unicodeSyllable["uVowel"] + "_lig"
    #                 if (self.data["kinzi"][key] and len(self.data["kinzi"][key])):
    #                     syllable["kinzi"] = self.data["kinzi"][key]
    #                     del syllable["uVowel"]
    #         if (unicodeSyllable.has_key ("anusvara")):
    #             key = unicodeSyllable["kinzi"] + unicodeSyllable["anusvara"] + "_lig"
    #             if (self.data["kinzi"][key] and len(self.data["kinzi"][key])):
    #                 syllable["kinzi"] = self.data["kinzi"][key]
    #                 del syllable["anusvara"]
                    
    #     if (unicodeSyllable["cons"] == u"ဉ"):
    #         if (unicodeSyllable.has_key("asat")):
    #             syllable["cons"] = self.data["cons"][u"ဥ"];
    #         elif (unicodeSyllable.has_key ("stack")):
    #             syllable["cons"] = self.data["cons"][u"ဉ_alt"];
    #         elif (unicodeSyllable.has_key("aVowel") and self.data["cons"][u"ဉာ_lig"]):
    #             syllable["cons"] = self.data["cons"][u"ဉာ_lig"]
    #             del syllable["aVowel"]
    #             # self hatoh can occur with aVowel, so no else
    #         if (unicodeSyllable.has_key ("hatoh")):
    #             syllable["hatoh"] = self.data["hatoh"][u"ှ_small"];
                
    #     elif (unicodeSyllable["cons"] == u"ဠ"):
    #         if (unicodeSyllable.has_key("hatoh")):
    #             syllable["hatoh"] = self.data["hatoh"][u"ှ_small"]:
                
    #     elif (unicodeSyllable["cons"] == u"ဈ" and len(self.data["cons"][u"ဈ"]) == 0):
    #         syllable["cons"] = self.data["cons"][u"စ"]
    #         syllable["yapin"] = self.data["yapin"][u"ျ"];
            
    #     elif (unicodeSyllable["cons"] == u"ဩ" and len(self.data["cons"][u"ဩ"]) == 0):
    #         syllable["cons"] = self.data["cons"][u"သ"];
    #         syllable["yayit"] = self.data["yayit"][u"ြ_wide"]

    #     elif (unicodeSyllable["cons"] == u"ဪ"  and len(self.data["cons"][u"ဪ"].) == 0):
    #         syllable["cons"] = self.data[u"သ"];
    #         syllable["yayit"] = self.data["ြ_wide"];
    #         syllable["eVowel"] = self.data[u"ေ"];
    #         syllable["aVowel"] = self.data[u"ာ"];
    #         syllable["asat"] = self.data[u"်"]

    #     elif (unicodeSyllable["cons"] == u"၎င်း" and  len(self.data["cons"][u"၎င်း"]) == 0):
    #         if (len(self.data[u"၎"])):
    #             syllable["cons"] = self.data["cons"][u"၎"] + self.data["cons"][u"င"] + \
    #                 self.data["asat"][u"်"] + self.data["visarga"][u"း"];
    #         else:
    #             syllable["cons"] = self.data["number"][u"၄"] + self.data["cons"][u"င"] + \
    #                 self.data["asat"][u"်"] + self.data["visarga"][u"း"];

    #     elif (unicodeSyllable["cons"] == u"န" or unicodeSyllable["cons"] == u"ည"):
    #         if (unicodeSyllable.has_key("stack") or unicodeSyllable.has_key("yapin") or
    #             unicodeSyllable.has_key("wasway") or unicodeSyllable.has_key("hatoh")
    #             or unicodeSyllable.has_key("lVowel")):
    #             syllable["cons"] = self.data["cons"][unicodeSyllable["cons"] + "_alt"]
        
    #     elif (unicodeSyllable["cons"] == u"ရ"):
    #         if (unicodeSyllable.has_key("yapin") or unicodeSyllable.has_key("wasway") or
    #             unicodeSyllable.has_key("lVowel")):
    #             syllable["cons"] = self.data["cons"][unicodeSyllable["cons"] + "_alt"]
    #         elif (unicodeSyllable.has_key("hatoh") and len(self.data["cons"][unicodeSyllable["cons"] + "_tall"])):
    #             syllable["cons"] = self.data["cons"][unicodeSyllable["cons"] + "_tall"];
        
    #     elif (unicodeSyllable["cons"] == u"ဦ"):
    #         if (len(self.data["cons"]["ဦ"]) == 0):
    #             syllable["cons"] = self.data["cons"]["ဥ"];
    #             syllable["uVowel"] = self.data["uVowel"]["ီ"];

    #     # stack with narrow upper cons
    #     if ((unicodeSyllable["cons"] == u"ခ" or unicodeSyllable["cons"] == u"ဂ" or
    #          unicodeSyllable["cons"] == u"င" or unicodeSyllable["cons"] == u"စ" or
    #          unicodeSyllable["cons"] == u"ဎ" or unicodeSyllable["cons"] == u"ဒ" or
    #          unicodeSyllable["cons"] == u"ဓ" or unicodeSyllable["cons"] == u"န" or
    #          unicodeSyllable["cons"] == u"ပ" or unicodeSyllable["cons"] == u"ဖ" or
    #          unicodeSyllable["cons"] == u"ဗ" or unicodeSyllable["cons"] == u"မ" or
    #          unicodeSyllable["cons"] == u"ဝ") and
    #         unicodeSyllable.has_key("stack") and self.data["stack"][unicodeSyllable["stack"]+"_narrow"] and
    #         len(self.data["stack"][unicodeSyllable["stack"]+"_narrow"]) > 0):
    #         syllable["stack"] = self.data["stack"][unicodeSyllable["stack"]+"_narrow"];

    #     # yapin variants
    #     if (unicodeSyllable.has_key("yapin") and
    #         (unicodeSyllable.has_key("wasway") or unicodeSyllable.has_key("hatoh"))):
    #         if (len(this.data["yapin"]["ျ_alt"])):
    #             syllable["yapin"] = this.data["yapin"]["ျ_alt"];
    #         else: # assume we have the ligatures
    #             key = u"ျ" + (unicodeSyllable.has_key("wasway") and u"ွ" or "") +
    #             (unicodeSyllable.has_key["hatoh"] and "ှ" or :"") + "_lig";
    #             if (this.data["yapin"][key]):
    #                 syllable["yapin"] = this.data["yapin"][key];
    #                 if (unicodeSyllable.has_key("wasway")):
    #                     del syllable["wasway"]
    #                 if (unicodeSyllable.has_key("hatoh")):
    #                     del syllable["hatoh"];
    #             else:
    #                 pass
    #                 #this.debug.print(key + " not found");
        
    #     if (unicodeSyllable.has_key ("wasway")):
    #         if (unicodeSyllable.has_key ("hatoh")):
    #             if (len(self.data["wasway"]["ွှ_small"])):
    #                 if (len(self.data["yayit"]["ြ" + upperVariant + widthVariant])):
    #                     syllable["yayit"] = self.data["yayit"]["ြ" + upperVariant + widthVariant];
    #                 else:
    #                     if (widthVariant == "_narrow"):
    #                         widthVariant = "";
    #                     syllable["yayit"] = self.data["yayit"]["ြ" + widthVariant]
    #                 syllable["wasway"] = self.data["wasway"]["ွှ_small"];
    #                 del syllable["hatoh"]
    #             elif (len(self.data["yayit"]["ြ_lower" + widthVariant])):
    #                 if (len(this.data["yayit"]["ြ_lower" + upperVariant + widthVariant])):
    #                     syllable["yayit"] = this.data["yayit"]["ြ_lower" + upperVariant + widthVariant];
    #                 else:
    #                     syllable["yayit"] = this.data["yayit"]["ြ_lower" + widthVariant];

    #         elif (len(self.data["yayit"]["ြွ" + upperVariant + widthVariant])):
    #             syllable["yayit"] = self.data["yayit"]["ြွ" + upperVariant + widthVariant];
    #             del syllable["wasway"]
                
    #         elif (len(self.data["yayit"]["ြွ" + widthVariant])):
    #             syllable["yayit"] = self.data["yayit"]["ြွ" + widthVariant];
    #             del syllable["wasway"]

    #         elif (len(self.data["yayit"]["ြ_lower_wide"])):
    #             if (len(self.data["yayit"]["ြ" + "_lower" + upperVariant + widthVariant])):
    #                 syllable["yayit"] = self.data["yayit"]["ြ" + "_lower" + upperVariant + widthVariant];
    #             else:
    #                 syllable["yayit"] = self.data["yayit"]["ြ" + "_lower" + widthVariant];

def get_available_encodings ():
    """
    return a list of available encodings.
    """
    return __CONVERTERS__.keys () + ['unicode']
        
def convert (text, from_encoding, to_encoding):
    """
    convert from one encoding to another.
    """
    # if type(text) != type(u''):
    #     try:
    #         text = text.decode ('utf-8')
    #     except:
    #         raise UnicodeDecodeError
        
    if from_encoding == to_encoding:
        raise ValueError ('from_encoding and to_encoding can not be equal')

    for encoding in [from_encoding, to_encoding]:
        if encoding not in get_available_encodings ():
            raise ValueError ('%s encoding is not available' %encoding)

    return __CONVERTERS__['zawgyi'].convertToUnicode (text)
    
        
__CONVERTERS__ = {}
for jFile in  ['zawgyi.json']: #'wininnwa.json', 'wwin_burmese.json']:
    try:
        import pkgutil
        data = pkgutil.get_data(__name__, 'data/' + jFile)
    except ImportError:
        import pkg_resources
        data = pkg_resources.resource_string(__name__, 'data/' + jFile)

    data = unicode(data.decode ('utf-8'))
    __CONVERTERS__[jFile[:jFile.find('.')]] = TlsMyanmarConverter (json.loads (data))
