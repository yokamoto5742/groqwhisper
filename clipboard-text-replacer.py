import pyperclip


def replace_text(text, replacements):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


# 置換のマッピングを定義
replacements = {
    "少子体": "硝子体",
    "少子体手術": "硝子体手術",
    # 他の置換ペアをここに追加できます
}

# クリップボードからテキストを取得
original_text = pyperclip.paste()
print(original_text)

# テキストを置換
replaced_text = replace_text(original_text, replacements)

# 置換されたテキストをクリップボードに戻す
pyperclip.copy(replaced_text)
print(replaced_text)
print("テキストが置換され、クリップボードにコピーされました。")
