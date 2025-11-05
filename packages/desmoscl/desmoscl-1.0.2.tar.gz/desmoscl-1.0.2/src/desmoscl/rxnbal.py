import numpy as np

# Module to write Desmos code for reaction balancing exercise

def bal (rxn,name,elem,comp,var,coeff):
    # Useful strings based on reaction data
    
    varstr = ''; varlist = ''; nvarlist = ''
    
    for cf in np.arange(0,comp):
        varstr += '"' + var[cf] + '"'
        varlist += var[cf]
        nvarlist += var[cf] + var[cf]
        if cf != comp-1:
            varstr += ','; varlist += ','; nvarlist += ','
    
    # Intro component
    
    print(name + 'intro:'); print()
    
    print('rxn0 = ' + rxn); print()
    for cf in np.arange(0,comp):
        print(var[cf] + 'val = ' + str(coeff[cf]))
    print(); print()
    
    # Balance components
    for el in np.arange(0,elem):
        print(name + 'balance' + str(el+1) + ':'); print()
        
        for cf in np.arange(0,comp):
            print(var[cf] + ' = ' + name + 'intro.script.' + var[cf] + 'val')
        print()
         
        print('ran = randomGenerator()')
        for cf in np.arange(0,comp):
            print(var[cf] + var[cf], '= ran.float(-999,-100)')
        print()
        
        s = 'df1 = parseEquation(this.latex).differenceFunction('
        s += varstr + ').evaluateAt(' + varlist + ')'
        print(s)
        
        print('df2 = when df1 < 0 numericValue("-${df1}") otherwise df1'); print()
        
        print('cor1 = when df2 <= 0.01 true otherwise false'); print()
        
        s = 'df3 = parseEquation(this.latex).differenceFunction('
        s += varstr + ').evaluateAt(' + nvarlist + ')'
        print(s)
        
        print('df4 = when df3 < 0 numericValue("-${df3}") otherwise df3'); print()
        
        print('cor2 = when df4 > 0.01 or isUndefined(df4) true otherwise false'); print()
        
        print('suffix: when cor1 and cor2 "✅" otherwise "❌"'); print()
        
        print('correct: when cor1 and cor2 true otherwise false'); print()
        
        print('disableEdit: when submit.pressCount > 1 true otherwise false'); print(); print()
        
    # Balance submit component
    
    print(name + 'balancesubmit:'); print()
    
    submitstr = ''
    for cf in np.arange(0,comp):
        submitstr += name + 'balance' + str(cf+1) + '.submitted'
        if cf != comp-1:
            submitstr += ' and '
    print('submit = when ' + submitstr + ' true otherwise false'); print(); print()
    
    # Final component
    
    print(name + 'final:'); print()
    
    print('rxn0 = ' + rxn); print()    
    for cf in np.arange(0,comp):
        s = 'rxn' + str(cf+1) + ' = substituteLatexVariable(rxn' + str(cf) + ','
        s += '`' + var[cf] + '`,' + name + 'table.script.' + var[cf] + ')'
        print(s)
    print()
    
    print('fb = when ' + name + 'table.script.cor "✅" otherwise "❌"')
    print(); print()
    
    # Table component
    
    print(name + 'table:'); print()
    
    print('maxrows = '+ str(comp)); print()
   
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        print('cellContent(' + scf + ',1): "' + var[cf] + '"')
    print()
    
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        s = 'df' + scf + ' = numericValue("${this.cellNumericValue(' + scf
        s += ',2)}-${' + name + 'intro.script.' + var[cf] + 'val}")'
        print(s)
        s = 'df' + scf + 'a = when df' + scf + ' >= 0 df' + scf
        s += ' otherwise numericValue("-${df' + scf + '}")'
        print(s)
    print()
    
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        s = 'cor' + scf + ' = when df' + scf + 'a < 0.01 true otherwise false'
        print(s)
    print()
        
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        print('cellSuffix(' + scf + ',2): when cor' + scf + ' "✅" otherwise "❌"')
    print()
    
    for cf in np.arange(0,comp):
        scf = str(cf+1); vcf = var[cf]
        print(vcf + ' = when this.cellContent(' + scf + ',2) = "" `' + vcf + '` otherwise')
        print('  when this.cellNumericValue(' + scf + ',2) = 1 `` otherwise')
        s = '    when this.cellNumericValue(' + scf + ',2) > 0 `${numericValue("\\round(${this.cellNumericValue('
        s += scf + ',2)},2)")}` otherwise `' + vcf + '`'
        print(s); print()
    
    s = 'cor = '
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        s += 'cor' + scf
        if cf != comp-1:
            s += ' and '
    print(s)
    print()
    
    print('correct: cor')
    print()
    
    for cf in np.arange(0,comp):
        scf = str(cf+1)
        print('cellEditable(' + scf + ',2): when submit.pressCount <= 1 true otherwise false')
