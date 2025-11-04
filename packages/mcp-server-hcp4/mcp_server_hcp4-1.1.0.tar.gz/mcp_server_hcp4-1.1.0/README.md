A Model Context Protocol (MCP) server that enables structured interactions with Microsoft Excel workbooks. Use it to read, write, query, and transform spreadsheet data via MCP-compliant clients.

### **Features**
1. Open and manage Excel workbooks and worksheets
2. Read/write cell ranges, rows, and columns
3. Append data and create tables
4. Evaluate formulas and recalculate sheets
5. Find/replace, filter, and basic data validation

### **MCP Capabilities**
1. open_workbook(path, mode="r|rw") -> { workbookId, sheets }
2. list_workbooks(root=?) -> [paths]
3. list_sheets(workbook) -> [names]
4. read_range(workbook, sheet, range) -> { values, types? }
5. write_range(workbook, sheet, range, values) -> { updated: count }
6. append_rows(workbook, sheet, rows) -> { appended: count }
7. find(workbook, sheet, query, matchCase=?, wholeCell=?) -> [addresses]
8. replace(workbook, sheet, query, replace, all=?) -> { replaced: count }
9. export_csv(workbook, sheet, range=?, path=?) -> { path }
10. export_json(workbook, sheet, range=?, path=?) -> { path }
11. save(workbook, path=?) -> { path }
12. close_workbook(workbook, save=?)

### **Resources**
1. workbook:list
2. sheet:list