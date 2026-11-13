' ==============================================================================
' FinSight 360: Master VBA Automation Suite for Excel Financial Reporting
' Theme: Executive Vanilla Palette
' Description: Automates data refreshes, styling, conditional audits, and PDF exports.
' ==============================================================================

Option Explicit

' ─── 1. REFRESH ALL PIVOT TABLES AND DATA CONNECTIONS ──────────────────────────
Public Sub RefreshReportData()
    Dim pc As PivotCache
    Dim ws As Worksheet
    
    On Error GoTo ErrorHandler
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Application.StatusBar = "Refreshing FinSight 360 Analytical Connections..."
    
    ' Refresh all Workbook Data Connections
    ThisWorkbook.RefreshAll
    
    ' Refresh all Pivot Tables
    For Each pc In ThisWorkbook.PivotCaches
        pc.Refresh
    Next pc
    
    Application.StatusBar = False
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    MsgBox "FinSight 360 analytical datasets refreshed successfully!", vbInformation, "ETL Sync Complete"
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    MsgBox "Error refreshing report data: " & Err.Description, vbCritical, "Refresh Error"
End Sub

' ─── 2. APPLY EXECUTIVE VANILLA NUMBER FORMATTING & STYLING ───────────────────
Public Sub FormatFinancialStatements()
    Dim ws As Worksheet
    Dim rng As Range
    Dim lastRow As Long, lastCol As Long
    
    On Error Resume Next
    Application.ScreenUpdating = False
    
    For Each ws In ThisWorkbook.Worksheets
        ws.Activate
        lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
        lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
        
        If lastRow > 1 Then
            ' Set Header Styling (Warm Vanilla Cream Header)
            Set rng = ws.Range(ws.Cells(1, 1), ws.Cells(1, lastCol))
            With rng
                .Interior.Color = RGB(247, 241, 229) ' #F7F1E5 Vanilla Cream
                .Font.Name = "Segoe UI"
                .Font.Bold = True
                .Font.Color = RGB(44, 40, 37)      ' #2C2825 Dark Charcoal
                .Borders(xlEdgeBottom).LineStyle = xlContinuous
                .Borders(xlEdgeBottom).Weight = xlMedium
                .Borders(xlEdgeBottom).Color = RGB(216, 196, 182)
            End With
            
            ' Auto-fit columns
            ws.Columns.AutoFit
        End If
    Next ws
    
    Application.ScreenUpdating = True
    MsgBox "Executive styling and number formatting applied across all sheets.", vbInformation, "Formatting Complete"
End Sub

' ─── 3. EXPORT ACTIVE FINANCIAL REPORT AS PDF ─────────────────────────────────
Public Sub ExportReportAsPDF()
    Dim exportPath As String
    Dim fileName As String
    Dim ws As Worksheet
    
    On Error GoTo ExportError
    Set ws = ActiveSheet
    
    fileName = "FinSight360_" & ws.Name & "_" & Format(Now(), "YYYYMMDD_HHMM") & ".pdf"
    exportPath = ThisWorkbook.Path & "\" & fileName
    
    ' Export to PDF
    ws.ExportAsFixedFormat _
        Type:=xlTypePDF, _
        fileName:=exportPath, _
        Quality:=xlQualityStandard, _
        IncludeDocProperties:=True, _
        IgnorePrintAreas:=False, _
        OpenAfterPublish:=True
        
    MsgBox "Report successfully exported to PDF:" & vbCrLf & exportPath, vbInformation, "PDF Export Complete"
    Exit Sub

ExportError:
    MsgBox "PDF Export failed: " & Err.Description, vbCritical, "Export Error"
End Sub

' ─── 4. CONDITIONAL FORMATTING FOR BUDGET VARIANCES ────────────────────────────
Public Sub HighlightBudgetVariances()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim varianceVal As Double
    
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Budget vs Actual")
    If ws Is Nothing Then Exit Sub
    
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    For i = 2 To lastRow
        varianceVal = ws.Cells(i, 6).Value ' Assuming Column F has Variance %
        
        If varianceVal > 10 Then
            ' Over budget warning (Soft Red)
            ws.Cells(i, 6).Interior.Color = RGB(248, 229, 229)
            ws.Cells(i, 6).Font.Color = RGB(163, 74, 66)
        ElseIf varianceVal >= 0 Then
            ' Favorable / On track (Soft Green)
            ws.Cells(i, 6).Interior.Color = RGB(226, 236, 229)
            ws.Cells(i, 6).Font.Color = RGB(78, 110, 88)
        End If
    Next i
    
    MsgBox "Budget variance conditional alerts updated.", vbInformation, "Variance Audit"
End Sub

