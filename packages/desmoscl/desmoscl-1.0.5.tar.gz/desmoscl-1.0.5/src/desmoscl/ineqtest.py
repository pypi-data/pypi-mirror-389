def inequality (names,eqns,variables,valueseq,valuesineq,strict,thr=0.01,inc=[[]],lock=True):
    # Module to write Desmos code for checking inequalities
    # The vectors names and ineqn must be of the same size
    # The vectors variables must be of the same size as the columns of valueseq or valuesineq
    # Each inequality is tested a different point
    # This differs from equation, which tests all equations at the same point
    # Each inequality is first tested at its boundary and then at an interior feasible point
    # Inequalities have to be matched exactly; there is no option of inexact matching
    #   the incidence matrix inc must be sized with inequalities as rows and variables as columns
    #   this matrix must contain only 0s and 1s
    
    import numpy as np
    import sys
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

    rows = np.size(names,0)
    cols = np.size(variables,0)
    
    cc = int(np.floor(np.log(cols)/np.log(10))+1) # zero-fill variable names based on total columns
    varrnd = ['var' + str(j+1).zfill(cc) for j in np.arange(0,cols)]

    if lock == False:
        print('showSubmitButton: False')
    
    # Test the boundaries of the inequalities
    for i in np.arange(0,rows):
        print(names[i] + ':'); print()
        
        print('ran = randomGenerator()')
        for j in np.arange(0,cols):
            print(varrnd[j] + ' = ran.float(-999,-100)')
        print()
        
        # Use incidence matrix to identify which variables occur in this inequality, and create lists accordingly
        varrndlist = ''; varstr = ''; varlist = ''; varilist = ''
        
        k = 0
        
        for j in np.arange(0,cols):
            if inc[i,j] == 1:
                if k > 0:
                    varrndlist += ','; varstr += ','; varlist += ','; varilist += ','    
                
                varrndlist += str(varrnd[j])
                varstr += str(variables[j])
                varlist += str(valueseq[i,j])
                varilist += str(valuesineq[i,j])
                k += 1
                    
        s = 'd0 = parseInequality(' + eqns[i] + ').differenceFunction('
        s += varstr + ').evaluateAt(' + varlist + ')'
        print(s)
        
        print('a0 = when d0 < 0 simpleFunction("-x","x").evaluateAt(d0) otherwise d0'); print()
        
        print('cor0 = when a0 <= ' + str(thr) + ' true otherwise false'); print()        
        
        s = 'd1 = parseInequality(this.latex).differenceFunction('
        s += varstr + ').evaluateAt(' + varlist + ')'
        print(s)
        
        print('a1 = when d1 < 0 simpleFunction("-x","x").evaluateAt(d1) otherwise d1'); print()
        
        print('cor1 = when a1 <= ' + str(thr) + ' true otherwise false'); print()

        s = 'd2 = parseInequality(this.latex).differenceFunction('
        s += varstr + ').evaluateAt(' + varrndlist + ')'
        print(s)
        
        print('a2 = when d2 < 0 simpleFunction("-x","x").evaluateAt(d2) otherwise d2'); print()
        
        print('cor2 = when a2 > ' + str(thr) + ' or isUndefined(a2) true otherwise false'); print()
        
        s = 'd3 = parseInequality(' + eqns[i] + ').differenceFunction('
        s += varstr + ').evaluateAt(' + varilist + ')'
        print(s)
        
        print('s3 = when d3 > 0 1 otherwise -1'); print()
        
        s = 'd4 = parseInequality(this.latex).differenceFunction('
        s += varstr + ').evaluateAt(' + varilist + ')'
        print(s)
        
        print('s4 = when d4 > 0 1 otherwise -1'); print()
        
        print('s34 = simpleFunction("a/b","a","b").evaluateAt(s3,s4)')
        print('cor34 = when s34 > 0 true otherwise false'); print()
        
        s = ('cors = when parseInequality(this.latex).isStrict false otherwise true')
        print(s); print()
        
        print('suffix: when cor0 and cor1 and cor2 and cor34 and cors "✅" otherwise "❌"'); print()
        print('correct: when cor0 and cor1 and cor2 and cor34 and cors true otherwise false'); print()

        if lock == True:
            print('disableEdit: when submit.pressCount > 1 true otherwise false'); print(); print()
        else:
            print('# disableEdit: when submit.pressCount > 1 true otherwise false'); print(); print()

