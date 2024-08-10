from indic_transliteration import sanscript

def devanagari_to_wx(text):
    return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.WX)

# Example usage
devanagari_text = "अग्निमीळे ईळे"
wx_notation = devanagari_to_wx(devanagari_text)
print(wx_notation)  # Output should be ILe