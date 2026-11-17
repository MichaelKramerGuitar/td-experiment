# clean: NOAA CSV (comment lines + header + rows) -> 3-column table.
# The File In DAT delivers the file as ONE cell of text, so we split it into lines ourselves.
def onCook(scriptOp):
    scriptOp.clear()
    src = scriptOp.inputs[0]
    text = '\n'.join(c.val for c in src.col(0)) if src.numCols == 1 else None
    lines = text.splitlines() if text is not None else [','.join(c.val for c in src.row(r)) for r in range(src.numRows)]
    header = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue                      # skip comments / blanks
        cells = [c.strip() for c in line.split(',')]
        if header is None:
            header = cells                # year,month,decimal date,average,deseasonalized,...
            scriptOp.appendRow(['decimal_date', 'average', 'deseasonalized'])
            continue
        row = dict(zip(header, cells))
        try:
            avg = float(row['average'])
        except (KeyError, ValueError):
            continue
        if avg < 0:                       # NOAA marks missing values with negative numbers
            continue
        scriptOp.appendRow([row['decimal date'], row['average'], row['deseasonalized']])
    return
