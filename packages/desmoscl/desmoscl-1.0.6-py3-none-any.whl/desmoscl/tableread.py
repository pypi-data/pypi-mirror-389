def tbl (file,tola=1.0,tolf=0.01,feedback='individual',samesheet=0,sheet='',skiprows=-1,nrows=-1,usecols="",lock=True):
    # Module to write Desmos code for fill-in-the-table question
    # Data, mode and format tables can be suppied in two ways
    # One method is to use three Excel sheets named data, mode and format
    # In this method, the sheets should only contain the relevant tables
    # For this method, samesheet is 0
    # Another method is to use any three non-overlapping regions in a single Excel sheet
    # This should be the only sheet in the Excel file
    # For this method, samesheet = 1f
    # The vectors skiprows, nrows and usecols should be 3-component vectors
    # The three components should correspond to data, mode and format

    import numpy as np
    import pandas as pd
    import sys
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    
    if samesheet == 0:
        datafrm = pd.read_excel(file, sheet_name='data')
    else:
        datafrm = pd.read_excel(file, sheet_name=sheet, skiprows=skiprows[0], nrows=nrows[0], usecols=usecols[0])    
    data = datafrm.to_numpy()
    
    if samesheet == 0:
        mode = pd.read_excel(file, sheet_name='mode').to_numpy()
    else:
        mode = pd.read_excel(file, sheet_name=sheet, skiprows=skiprows[1], nrows=nrows[1], usecols=usecols[1]).to_numpy()
    
    if samesheet == 0:
        frmt = pd.read_excel(file, sheet_name='format').to_numpy()
    else:
        frmt = pd.read_excel(file, sheet_name=sheet, skiprows=skiprows[2], nrows=nrows[2], usecols=usecols[2]).to_numpy()
    
    rows = np.size(data,0)
    cols = np.size(data,1)
    rr = int(np.floor(np.log(rows)/np.log(10))+1) # zero-fill variable names based on total rows
    cc = int(np.floor(np.log(cols)/np.log(10))+1) # zero-fill variable names based on total columns
    
    cor = ''; count = 0 # string to collect correctness variables for entire table
    
    for j in np.arange(0,len(datafrm.columns)): # print headers
        cellij = '(' + str(0) + ',' + str(j+1) + ')'
        print('cellContent' + cellij + ': "' + datafrm.columns[j] + '"')
    print()
    
    expcount = 0 # number of expressions without = sign
    varmax = 0 # maxnumber of variables in a single expression without = sign
            
    for i in np.arange(0,rows):
        if feedback == 'row':
            cori = ''; counti = 0; # string to collect correctness variables for current row
        
        for j in np.arange(0,cols):
            cellij = '(' + str(i+1) + ',' + str(j+1) + ')'
            
            if mode[i,j] == 'display': # entries displayed verbatim
                if frmt[i,j] == 'text' or frmt[i,j] == 'expression' or frmt[i,j] == 'equation':
                    print('cellContent' + cellij + ': "' + data[i,j] + '"')
                    print()
                if frmt[i,j] == 'exact' or frmt[i,j] == 'number':
                    print('cellContent' + cellij + ': `' + str(data[i,j]) + '`')
                
            if mode[i,j] == 'test': # entries tested for
                if frmt[i,j] == 'text' or frmt[i,j] == 'exact' or frmt[i,j] == 'expression' or frmt[i,j] == 'equation' or frmt[i,j] == 'number':
                    ij = str(i+1).zfill(rr) + str(j+1).zfill(cc)
                    
                    if frmt[i,j] == 'text' and type(data[i,j]) == str:
                        print('cor' + ij + ' = when this.cellContent' + cellij + ' = "' + data[i,j] + '" true otherwise false')
                    elif frmt[i,j] == 'text' and (type(data[i,j]) == int or type(data[i,j]) == float):
                        print('cor' + ij + ' = when this.cellContent' + cellij + ' = "' + str(data[i,j]) + '" true otherwise false')
                    elif frmt[i,j] == 'exact' and (type(data[i,j]) == int or type(data[i,j]) == float):
                            print('cor' + ij + ' = when this.cellNumericValue' + cellij + ' = ' + str(data[i,j]) + ' true otherwise false')
                    elif frmt[i,j] == 'exact' and type(data[i,j]) == str: # used for variable names, e.g., row headers in a simplex tableau
                            print('cor' + ij + ' = when this.cellContent' + cellij + ' = `' + data[i,j] + '` true otherwise false')
                            
                    if frmt[i,j] == 'number': # number with tolerance range
                        dij = 'd' + ij
                        daij = 'a' + ij
                        fij = 'f' + ij
                        faij = 'fa' + ij
                        
                        print(dij + ' = simpleFunction("x-y","x","y").evaluateAt(this.cellNumericValue' + cellij + ',' + str(data[i,j]) + ')')
                        print(daij + ' = when ' + dij + ' < 0 simpleFunction("-x","x").evaluateAt(' + dij + ') otherwise ' + dij)
                        print(fij + ' = simpleFunction("x/y","x","y").evaluateAt(' + daij + ',' + str(data[i,j]) + ')')
                        print(faij + ' = when ' + fij + ' < 0 simpleFunction("-x","x").evaluateAt(' + fij + ') otherwise ' + fij)
                        print('cor' + ij + ' = when ' + daij + ' < ' + str(tola) + ' or ' + faij + ' < ' + str(tolf) + ' true otherwise false')                     
                    
                    if frmt[i,j] == 'expression': # expression without equal sign
                        expcount += 1
                        
                        dataij = data[i,j].replace('[','').replace(']]','').split('],')

                        vars = int(dataij[2])
                        if vars > varmax:
                            varmax = vars
                        
                        cc = int(np.floor(np.log(vars)/np.log(10))+1) # zero-fill variable names based on total variables
                        varrnd = ['var' + str(j+1).zfill(cc) for j in np.arange(0,vars)]
                        varrndlist = str(varrnd).replace('[','').replace(']','').replace("'",'')
                        
                        print('exp' + ij + ' = ' + dataij[0])
                        
                        fij = 'f' + ij
                        gij = 'g' + ij
                        dij = 'd' + ij
                        aij = 'a' + ij
                        
                        print(fij + ' = simpleFunction(exp' + ij + ',' + dataij[1] + ').evaluateAt(' + varrndlist + ')')
                        print(gij + ' = simpleFunction(this.cellContent' + cellij + ',' + dataij[1] + ').evaluateAt(' + varrndlist + ')')
                        print(dij + ' = simpleFunction("x-y","x","y").evaluateAt(' + fij + ',' + gij + ')')
                        print(aij + ' = when ' + dij + ' < 0 simpleFunction("-x","x").evaluateAt(' + dij + ') otherwise ' + dij)
                        print('cor' + ij + ' = when ' + aij + ' < tola true otherwise false')
                    
                    if frmt[i,j] == 'equation': # equation
                        dataij = data[i,j].replace('[','').replace(']]','').split('],')
                        print('eq' + ij + ' = ' + dataij[0])
                        
                        dij = 'd' + ij
                        aij = 'a' + ij
                        print(dij + ' = parseEquation(this.cellContent' + cellij + ').differenceFunction(' + dataij[1] + ').evaluateAt(' + dataij[2] + ')')
                        print(aij + ' = when ' + dij + ' < 0 simpleFunction("-x","x").evaluateAt(' + dij + ') otherwise ' + dij)
                        print('cor' + ij + ' = when ' + aij + ' < tola true otherwise false')
                        
                    if feedback == 'individual': # feedback requested for individual cells (default option)
                        print('cellSuffix' + cellij + ': when cor' + ij + ' "✅" otherwise "❌"')
                    
                    if lock == True:
                        print('cellEditable' + cellij + ': when submit.pressCount <= 1 true otherwise false')
                    else:
                        print('# cellEditable' + cellij + ': when submit.pressCount <= 1 true otherwise false')
                    
                    if count == 0:
                        cor += 'cor' + ij
                    else:
                        cor += ' and cor' + ij                           
                    count += 1
                    
                    if feedback == 'row':
                        if counti == 0:
                            cori += 'cor' + ij
                        else:
                            cori += ' and cor' + ij
                        counti += 1
                    print()
        if feedback == 'row':
            cellij1 = '(' + str(i+1) + ',' + str(j+2) + ')'
            print('cellContent' + cellij1 + ': when ' + cori + ' "✅" otherwise "❌"')
            print()
        
    if expcount > 0:
        print('tola = ' + str(tola))
        print()
        print('ran = randomGenerator()')    
    
        cc = int(np.floor(np.log(varmax)/np.log(10))+1) # zero-fill variable names based on total variables
        varrnd = ['var' + str(j+1).zfill(cc) for j in np.arange(0,varmax)]
        for j in np.arange(0,varmax):
            print(varrnd[j] + ' = ran.float(-999,-100)')
        
    print('correct: ' + cor)
