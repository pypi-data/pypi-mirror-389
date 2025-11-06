def equation (names,eqns,variables,values,thr=0.01,exact=0,inc=[[]],lock=True):
    # Module to write Desmos code for checking equations
    # The vectors names and eqns must be of the same size
    # The vectors variables and values must be of the same size
    # If equations have to be matched exactly (exact == 1):
    #   the incidence matrix inc must be sized with equations as rows and variables as columns
    #   this matrix must contain only 0s and 1s

    import numpy as np
    import sys
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    
    rows = np.size(names,0)
    cols = np.size(variables,0)
    
    cc = int(np.floor(np.log(cols)/np.log(10))+1) # zero-fill variable names based on total columns
    varrnd = ['var' + str(j+1).zfill(cc) for j in np.arange(0,cols)]
    
    # Equations do not have to be exactly matched; create lists outside loop
    if exact == 0: 
        varrndlist = str(varrnd).replace('[','').replace(']','').replace("'",'')   
        varstr = str(variables).replace('[','').replace(']','').replace("'",'')        
        varlist = str(values).replace('[','').replace(']','')
        varlist = varlist.replace("'",'') # remove double quotes from any strings

    if lock == False:
        print('showSubmitButton: False')

    for i in np.arange(0,rows):
        print(names[i] + ':'); print()
        
        print('ran = randomGenerator()')
        for j in np.arange(0,cols):
            print(varrnd[j] + ' = ran.float(-999,-100)')
        print()
        
        if exact == 0:        
            s = 'd1 = parseEquation(this.latex).differenceFunction('
            s += varstr + ').evaluateAt(' + varlist + ')'
            print(s)
            
            print('a1 = when d1 < 0 simpleFunction("-x","x").evaluateAt(d1) otherwise d1'); print()
            
            print('cor1 = when a1 <= ' + str(thr) + ' true otherwise false'); print()
    
            s = 'd2 = parseEquation(this.latex).differenceFunction('
            s += varstr + ').evaluateAt(' + varrndlist + ')'
            print(s)
            
            print('a2 = when d2 < 0 simpleFunction("-x","x").evaluateAt(d2) otherwise d2'); print()
            
            print('cor2 = when a2 > ' + str(thr) + ' or isUndefined(a2) true otherwise false'); print()
            
            print('suffix: when cor1 and cor2 "✅" otherwise "❌"'); print()
            print('correct: when cor1 and cor2 true otherwise false'); print()
        
        elif exact == 1:
            # Use incidence matrix to identify which variables occur in this equation, and create lists accordingly
            varrndlist = ''; varstr = ''; varlist = ''
            k = 0
            for j in np.arange(0,cols):
                if inc[i,j] == 1:
                    if k > 0:
                        varrndlist += ','; varstr += ','; varlist += ','                 
                    varrndlist += str(varrnd[j])
                    varstr += str(variables[j])
                    varlist += str(values[j])
                    k += 1
                        
            s = 'd0 = parseEquation(' + eqns[i] + ').differenceFunction('
            s += varstr + ').evaluateAt(' + varlist + ')'
            print(s)
            
            print('a0 = when d0 < 0 simpleFunction("-x","x").evaluateAt(d0) otherwise d0'); print()
            
            print('cor0 = when a0 <= ' + str(thr) + ' true otherwise false'); print()        
            
            s = 'd1 = parseEquation(this.latex).differenceFunction('
            s += varstr + ').evaluateAt(' + varlist + ')'
            print(s)
            
            print('a1 = when d1 < 0 simpleFunction("-x","x").evaluateAt(d1) otherwise d1'); print()
            
            print('cor1 = when a1 <= ' + str(thr) + ' true otherwise false'); print()
    
            s = 'd2 = parseEquation(this.latex).differenceFunction('
            s += varstr + ').evaluateAt(' + varrndlist + ')'
            print(s)
            
            print('a2 = when d2 < 0 simpleFunction("-x","x").evaluateAt(d2) otherwise d2'); print()
            
            print('cor2 = when a2 > ' + str(thr) + ' or isUndefined(a2) true otherwise false'); print()
            
            print('suffix: when cor0 and cor1 and cor2 "✅" otherwise "❌"'); print()
            print('correct: when cor0 and cor1 and cor2 true otherwise false'); print()

        if lock == True:
            print('disableEdit: when submit.pressCount > 1 true otherwise false'); print(); print()
        else:
            print('# disableEdit: when submit.pressCount > 1 true otherwise false'); print(); print()
