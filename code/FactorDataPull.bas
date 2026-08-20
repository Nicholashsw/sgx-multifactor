Attribute VB_Name = "FactorDataPull"
'==================================================================================
' FactorDataPull.bas
' SGX systematic multi-factor data puller (Bloomberg Excel API)
' NTU FYP A1083
'
' WHAT IT DOES
'   Reads tickers from the Universe sheet, writes one BDH array formula per
'   ticker per field into a hidden staging sheet, waits for Bloomberg to
'   refresh, then reshapes the blocks into a clean panel on FactorData:
'       Date | Ticker | CUR_MKT_CAP | RETURN_COM_EQY | TOT_DEBT_TO_COM_EQY |
'       EQY_DVD_YLD_IND | PX_VOLUME | RETURN_ON_ASSET
'
' ENTRY POINTS (assign a button to PullMissingFactorData)
'   PullMissingFactorData     primary one-click pull (write + wait + harvest)
'   BackupStep1_WriteFormulas two-step fallback for unreliable async refresh:
'   BackupStep2_Harvest       run step 1, watch staging finish, run step 2
'   ExportFactorDataCSV       export FactorData as a Python-friendly CSV
'
' EDIT POINTS
'   CONFIG block below (dates, sheet names, ticker column)
'   FactorFields()  single place to change the field list
'
' POINT-IN-TIME WARNING (do not delete this comment)
'   RETURN_COM_EQY, TOT_DEBT_TO_COM_EQY and RETURN_ON_ASSET are fiscal-period
'   fields. Bloomberg timestamps them at period end, not announcement date,
'   and restated values overwrite history. They are NOT point-in-time. The
'   Python pipeline must forward-fill within ticker and then shift forward by
'   the reporting embargo before any signal is computed. Market cap, dividend
'   yield and volume are observation-dated and need no embargo.
'==================================================================================

Option Explicit

'================================ CONFIG ===========================================
Private Const UNIVERSE_SHEET As String = "Universe"
Private Const TICKER_COL As String = "A"
Private Const TICKER_START_ROW As Long = 2
Private Const OUTPUT_SHEET As String = "FactorData"
Private Const STAGING_SHEET As String = "_FactorStaging"

Private Const START_YEAR As Long = 2010
Private Const START_MONTH As Long = 1
Private Const START_DAY As Long = 31

' Columns each ticker block occupies on staging: 1 date col + N field cols + 1 gap
Private Const MAX_MONTHS As Long = 400
Private Const REFRESH_TIMEOUT_SECS As Long = 300
Private Const POLL_SECS As Long = 5
'===================================================================================

Private Function FactorFields() As Variant
    ' Single edit point for the field list. Order defines output column order.
    FactorFields = Array("CUR_MKT_CAP", "RETURN_COM_EQY", _
                         "TOT_DEBT_TO_COM_EQY", "EQY_DVD_YLD_IND", _
                         "PX_VOLUME", "RETURN_ON_ASSET")
End Function

Private Function StartDateStr() As String
    StartDateStr = Format(DateSerial(START_YEAR, START_MONTH, START_DAY), "yyyymmdd")
End Function

Private Function EndDateStr() As String
    ' Last completed month end.
    Dim d As Date
    d = DateSerial(Year(Date), Month(Date), 1) - 1
    EndDateStr = Format(d, "yyyymmdd")
End Function

Private Function ReadTickers() As Collection
    Dim ws As Worksheet, c As New Collection, r As Long, v As String
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(UNIVERSE_SHEET)
    On Error GoTo 0
    If ws Is Nothing Then
        Err.Raise vbObjectError + 1, , "Universe sheet not found: " & UNIVERSE_SHEET
    End If
    r = TICKER_START_ROW
    Do While Len(Trim(ws.Range(TICKER_COL & r).Value)) > 0
        v = Trim(ws.Range(TICKER_COL & r).Value)
        If InStr(1, v, "Equity", vbTextCompare) > 0 Then c.Add v
        r = r + 1
    Loop
    If c.Count = 0 Then
        Err.Raise vbObjectError + 2, , "No tickers found in " & UNIVERSE_SHEET & "!" & TICKER_COL
    End If
    Set ReadTickers = c
End Function

Private Function GetOrCreateSheet(ByVal name As String, ByVal hidden As Boolean) As Worksheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(name)
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        ws.name = name
    Else
        ws.Cells.Clear
    End If
    If hidden Then ws.Visible = xlSheetHidden Else ws.Visible = xlSheetVisible
    Set GetOrCreateSheet = ws
End Function

Private Function BlockWidth() As Long
    BlockWidth = 1 + (UBound(FactorFields()) - LBound(FactorFields()) + 1) + 1
End Function

'============================ STEP 1: WRITE FORMULAS ================================
Public Sub BackupStep1_WriteFormulas()
    Dim stg As Worksheet, tickers As Collection, flds As Variant
    Dim i As Long, t As Long, col As Long, fldList As String

    Set stg = GetOrCreateSheet(STAGING_SHEET, True)
    Set tickers = ReadTickers()
    flds = FactorFields()

    fldList = ""
    For i = LBound(flds) To UBound(flds)
        If Len(fldList) > 0 Then fldList = fldList & ","
        fldList = fldList & flds(i)
    Next i

    Application.ScreenUpdating = False
    For t = 1 To tickers.Count
        col = (t - 1) * BlockWidth() + 1
        stg.Cells(1, col).Value = tickers(t)
        ' One BDH per ticker pulling all fields at once, monthly, calendar days,
        ' spilling Date + one column per field.
        stg.Cells(2, col).Formula = _
            "=BDH(""" & tickers(t) & """,""" & fldList & """,""" & _
            StartDateStr() & """,""" & EndDateStr() & _
            """,""Per=cm"",""Days=A"",""Fill=NA"",""Dates=S"")"
    Next t
    Application.ScreenUpdating = True

    Debug.Print "Step 1 complete: " & tickers.Count & " BDH blocks written to " & STAGING_SHEET
End Sub

'============================ STEP 2: HARVEST =======================================
Public Sub BackupStep2_Harvest()
    Dim stg As Worksheet, outWs As Worksheet, tickers As Collection, flds As Variant
    Dim t As Long, col As Long, r As Long, f As Long, outRow As Long
    Dim d As Variant, v As Variant

    On Error Resume Next
    Set stg = ThisWorkbook.Worksheets(STAGING_SHEET)
    On Error GoTo 0
    If stg Is Nothing Then
        Err.Raise vbObjectError + 3, , "Run Step 1 first: staging sheet missing"
    End If

    Set tickers = ReadTickers()
    flds = FactorFields()
    Set outWs = GetOrCreateSheet(OUTPUT_SHEET, False)

    outWs.Cells(1, 1).Value = "Date"
    outWs.Cells(1, 2).Value = "Ticker"
    For f = LBound(flds) To UBound(flds)
        outWs.Cells(1, 3 + f - LBound(flds)).Value = flds(f)
    Next f

    outRow = 2
    For t = 1 To tickers.Count
        col = (t - 1) * BlockWidth() + 1
        For r = 2 To 2 + MAX_MONTHS
            d = stg.Cells(r, col).Value
            If IsEmpty(d) Or Not IsDate(d) Then
                If r > 2 Then Exit For
            Else
                outWs.Cells(outRow, 1).Value = CDate(d)
                outWs.Cells(outRow, 2).Value = tickers(t)
                For f = LBound(flds) To UBound(flds)
                    v = stg.Cells(r, col + 1 + f - LBound(flds)).Value
                    If IsError(v) Then
                        outWs.Cells(outRow, 3 + f - LBound(flds)).Value = ""
                    ElseIf VarType(v) = vbString Then
                        If InStr(v, "#") > 0 Then
                            outWs.Cells(outRow, 3 + f - LBound(flds)).Value = ""
                        Else
                            On Error Resume Next
                            outWs.Cells(outRow, 3 + f - LBound(flds)).Value = CDbl(v)
                            On Error GoTo 0
                        End If
                    Else
                        outWs.Cells(outRow, 3 + f - LBound(flds)).Value = v
                    End If
                Next f
                outRow = outRow + 1
            End If
        Next r
    Next t

    outWs.Columns(1).NumberFormat = "yyyy-mm-dd"
    outWs.Rows(1).Font.Bold = True
    outWs.Columns.AutoFit

    Debug.Print "Step 2 complete: " & (outRow - 2) & " panel rows on " & OUTPUT_SHEET
End Sub

'============================ ONE-CLICK ============================================
Public Sub PullMissingFactorData()
    Dim t0 As Double, stg As Worksheet, pending As Boolean, r As Range

    BackupStep1_WriteFormulas
    Set stg = ThisWorkbook.Worksheets(STAGING_SHEET)

    ' Poll until Bloomberg's loading sentinel clears or timeout.
    t0 = Timer
    Do
        Application.Calculate
        DoEvents
        pending = False
        For Each r In stg.UsedRange.Cells
            If VarType(r.Value) = vbString Then
                If InStr(1, r.Value, "Requesting", vbTextCompare) > 0 _
                   Or InStr(1, r.Value, "#N/A Requesting", vbTextCompare) > 0 Then
                    pending = True
                    Exit For
                End If
            End If
        Next r
        If Not pending Then Exit Do
        Application.Wait Now + TimeSerial(0, 0, POLL_SECS)
    Loop While Timer - t0 < REFRESH_TIMEOUT_SECS

    If pending Then
        MsgBox "Bloomberg refresh did not complete within " & REFRESH_TIMEOUT_SECS & _
               "s. Wait for the staging sheet to finish, then run BackupStep2_Harvest.", _
               vbExclamation, "FactorDataPull"
        Exit Sub
    End If

    BackupStep2_Harvest
    MsgBox "FactorData panel built.", vbInformation, "FactorDataPull"
End Sub

'============================ CSV EXPORT ===========================================
Public Sub ExportFactorDataCSV()
    Dim ws As Worksheet, path As String, f As Integer
    Dim r As Long, c As Long, lastR As Long, lastC As Long, line As String, v As Variant

    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(OUTPUT_SHEET)
    On Error GoTo 0
    If ws Is Nothing Then
        MsgBox "No FactorData sheet. Run PullMissingFactorData first.", vbExclamation
        Exit Sub
    End If

    path = ThisWorkbook.path & Application.PathSeparator & "factor_data.csv"
    lastR = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastC = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column

    f = FreeFile
    Open path For Output As #f
    For r = 1 To lastR
        line = ""
        For c = 1 To lastC
            v = ws.Cells(r, c).Value
            If c = 1 And r > 1 And IsDate(v) Then v = Format(v, "yyyy-mm-dd")
            If Len(line) > 0 Then line = line & ","
            line = line & Replace(CStr(v), ",", ";")
        Next c
        Print #f, line
    Next r
    Close #f

    MsgBox "Exported " & (lastR - 1) & " rows to " & path, vbInformation, "FactorDataPull"
End Sub
