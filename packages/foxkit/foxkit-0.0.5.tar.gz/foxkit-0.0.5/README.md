
```python-repl
from foxkit.file.excel_tools import Sink2Excel,Row,Cell,CellDataType

if __name__ == '__main__':
  
    with Sink2Excel() as sink:
        sink.write(
            headers=Row(Cell(val='ID'),Cell(val='头像'),Cell(val='名称'),Cell(val='年龄')),
            rows=[
                Row(Cell(val='1001'),Cell(val='https://pic.cnblogs.com/face/83005/20250225134909.png',data_type=CellDataType.PIC),Cell(val='章三'),Cell(val=18)),
                Row(Cell(val='1001'),Cell(val='https://pic.cnblogs.com/face/2124951/20211014230234.png',data_type=CellDataType.PIC),Cell(val='章三'),Cell(val=18)),
                Row(Cell(val='1001'),Cell(val='https://pic.cnblogs.com/face/2124951/20211014230234.png',data_type=CellDataType.PIC),Cell(val='章三'),Cell(val=18)),
                Row(Cell(val='1001'),Cell(val='https://pic.cnblogs.com/face/2124951/20211014230234.png',data_type=CellDataType.PIC),Cell(val='章三'),Cell(val=18))

            ],
            sheet_name='用户信息',
            sequence=True
        )
        sink.sink_file('./test.xlsx')
```
