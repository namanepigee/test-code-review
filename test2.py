def parse_barclay_data(file_name):
    # Initialize headers according to the excel sheet
    
    headers = [
        ["Bank Name", "C"],
        ["Account Number", "C"],
        ["Account Name", "C"],
        ["Currency", "C"],
        ["Total Payment Amount / Payment Count", "C"],
        ["Total Receipt Amount / Receipt Count", "C"],
        ["Transaction Count", "C"],
    ]
    # Get reference to the sheet
    sheet_for_header = open_sheet(file_name, None)
    # get all the headers value
    headersdata = parse_headers(sheet_for_header, headers)
    dataheaders = {
        "account_number": headersdata[0],
        "account_name": headersdata[1],
        "currency": headersdata[2],
        "bank_name": headersdata[3],

        "payment_amount": headersdata[4],
        "receipt_amount": headersdata[5],
        "transaction_count": headersdata[6],
    }
    header_row = find_header_row(sheet_for_header, "Ledger Balance")
    sheet_for_table = open_sheet(file_name, header_row)
    table_data, total_credit, debit_amount = parse_table_data1(sheet_for_table)

    headersdata[4] = headersdata[4].split('/')[0]
    headersdata[5] = headersdata[5].split('/')[0]

    headersdata[4] = headersdata[4].replace(",", "")
    headersdata[5] = headersdata[5].replace(",", "")

    try:
        headersdata[4] = 0 if math.isnan(float(headersdata[4])) else Decimal(headersdata[4])
    except Exception as e:
        print("Exception e:", str(e))
        headersdata[4] = 0
    try:
        headersdata[5] = 0 if math.isnan(float(headersdata[5])) else Decimal(headersdata[5])
    except Exception as e:
        print("Exception e:", str(e))
        headersdata[5] = 0
    headersdata[4] = -abs(headersdata[4])
    dataheaders.update({"payment_amount": -abs(headersdata[4])})
    dataheaders.update({"receipt_amount": headersdata[5]})

    # error_message = ""
    # excluded_fields = {"debit", "Receivable_Amount", "payment_amount", "receipt_amount", "transaction_count"}
    # if dataheaders:
    #     blank_columns = []
    #     blank_columns += [
    #         key for key, value in dataheaders.items() 
    #         if key not in excluded_fields and 
    #         (pd.isna(value) or (isinstance(value, str) and value.strip() == "")) and 
    #         not isinstance(value, (int, Decimal))  
    #     ]
        
    # for row in table_data:
    #     blank_columns += [key for key, value in row.items() if key not in excluded_fields and not value and not isinstance(value, (int, float))]

    #     if blank_columns:
    #         error_message = f"Columns {blank_columns} are blank"
    #         return None, None, None, error_message
    error_message = ""
    excluded_fields = {"debit", "Receivable_Amount", "payment_amount", "receipt_amount", "transaction_count"}
    
    # ===== MODIFIED ERROR CHECKING SECTION =====
    if dataheaders:
        blank_columns = []
        # Check header fields first
        for key, value in dataheaders.items():
            if (key not in excluded_fields and 
                (pd.isna(value) or (isinstance(value, str) and value.strip() == "")) and 
                not isinstance(value, (int, Decimal))):
                
                # Find the actual location in the sheet
                location = "unknown"
                for row_idx in range(sheet_for_header.nrows):
                    for col_idx in range(sheet_for_header.ncols):
                        cell_val = str(sheet_for_header.cell_value(row_idx, col_idx))
                        if key.replace("_", " ").lower() in cell_val.lower():
                            location = f"row {row_idx+1}, col {col_idx+1}"
                            break
                    if location != "unknown":
                        break
                
                blank_columns.append(f"{key} (missing at {location})")

    # Check transaction data
    transaction_errors = []
    for row_idx, row in enumerate(table_data, 1):  # row_idx starts at 1
        row_errors = []
        for key, value in row.items():
            if (key not in excluded_fields and not value and 
                not isinstance(value, (int, float, Decimal))):
                
                # Find column position in the table
                col_pos = "unknown"
                if hasattr(sheet_for_table, 'ncols'):
                    for col_idx in range(sheet_for_table.ncols):
                        header_val = str(sheet_for_table.cell_value(header_row, col_idx))
                        if key.lower() in header_val.lower():
                            col_pos = f"col {col_idx+1}"
                            break
                
                row_errors.append(f"{key} at row {header_row + row_idx + 1}, {col_pos}")
        
        if row_errors:
            transaction_errors.append(f"Row {header_row + row_idx + 1}: {', '.join(row_errors)}")

    # Combine all errors
    if blank_columns:
        error_message += f"Missing header fields: {', '.join(blank_columns)}. "
    if transaction_errors:
        error_message += f"Missing transaction fields: {'; '.join(transaction_errors)}"
    
    if error_message:
        return None, None, None, error_message

    for obj in table_data:
        obj.update(dataheaders)
        obj.update({"error_message": error_message})
        import time
    return table_data, headersdata[4], headersdata[5], None

