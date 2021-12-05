import re

class SymbolList(object):
    @staticmethod
    def get_default_text():
        return """
            EURUSD AUDJPY AUDUSD CADJPY USDCAD 
        """

    @staticmethod
    def __new__(cls, text:str):
        if len(text) == 0:
            text = cls.get_default_text()
        seq = text.strip().split(' ')
        symbols = [str(s) for s in seq]
        return symbols

class InputBoolean(object):
    @staticmethod
    def __new__(cls, text:str):
        boolean = bool(int(text))
        return boolean

class Tech_Dict(object):
    @staticmethod
    def get_default_text():
        return """
            ma 5 10 25 50 100 150 200 250 ;
            bb (20,2,2,0) (20,3,3,0) (20,4,4,0) (40,2,2,0) (40,3,3,0) (40,4,4,0) ;
            std (5,1) (20,1) (50,1) (100,1) (150,1) (250,1) ;
            rsi 5 15 25 50 100 150 250 ;
            stocOsci (5,3,3,0,0) (14,3,3,0,0) (21,14,14,0,0) ;
            macd (12,26,9) (19,39,9) ;
        """

    @staticmethod
    def get_splited_text(text:str):
        splited_text = [t.strip() for t in text.split(';') if len(t.strip()) > 0]

        return splited_text

    @staticmethod
    def text_to_dic(splited_text):
        dic = {}
        for raw_text in splited_text:
            text = raw_text.split(' ', 1)
            dic[text[0]] = text[1]
        return dic

    @staticmethod
    def get_params(param_text):
        # tuple-based params: [(20,2,2,0),(20,3,3,0),(20,4,4,0),(40,2,2,0),(40,3,3,0),(40,4,4,0)]
        regex = r"\(\S+?\)"
        results = re.findall(regex, param_text)
        if results:
            params = []
            for result in results:
                param = [int(r.replace('(', '').replace(')', '')) for r in result.split(',')]
                param = tuple(param)
                params.append(param)
        # list-based params: [5,10,25,50,100,150,200,250]
        else:
            params = [int(p) for p in param_text.split(' ')]
        return params

    @staticmethod
    def __new__(cls, text:str):
        """
        tech_params = {
            'ma': [5,10,25,50,100,150,200,250],
            'bb': [(20,2,2,0),(20,3,3,0),(20,4,4,0),(40,2,2,0),(40,3,3,0),(40,4,4,0)],
            'std': [(5,1),(20,1),(50,1),(100,1),(150,1),(250,1)],
            'rsi': [5,15,25,50,100,150,250],
            'stocOsci': [(5,3,3,0,0),(14,3,3,0,0),(21,14,14,0,0)],
            'macd': [(12,26,9),(19,39,9)]
        }
        """
        if len(text) == 0:
            text = cls.get_default_text()
        params = {}
        splited_text = cls.get_splited_text(text)
        raw_dic = cls.text_to_dic(splited_text)
        for k, param_text in raw_dic.items():
            params[k] = cls.get_params(param_text)
        return params

# class Symbols_Descriptor:
#     def __init__(self):
#         self._symbols = []
#
#     def __get__(self, instance, owner):
#         return self._symbols
#
#     def __set__(self, instance, value):
#         self._symbols = [str(v) for v in value]
#
# class SymbolList(object):
#     symbols = Symbols_Descriptor()
#
#     def __init__(self, seq):
#         self.symbols = seq
#
#     def __call__(self):
#         return self.symbols
#
# class tech_params_Descriptor:
#     def __init__(self):
#         pass