# Loads the timing tables from the Folder parameter.
L = me.parent()
folder = L.par.Folder.eval()
L.op('lines').text = open(folder + '/lyrics_lines.tsv', encoding='utf-8').read()
L.op('words').text = open(folder + '/lyrics_words.tsv', encoding='utf-8').read()
