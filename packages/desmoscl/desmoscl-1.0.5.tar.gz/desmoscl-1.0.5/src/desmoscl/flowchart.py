def diagram(exps,blocks,streams,labels,size=[1000,400],bor=[-10,10,-10,10],font=0.8,tip=0.3,
            ang=math.pi/12,tipv=0.3,angv=math.pi/12,display=''):
    # Module to write Desmos console code to render a chemical process block flow diagram (BFD) or flowchart
    # The output of this code should be pasted into an html file

    import numpy as np
    import math
    import sys
    import io

    np.set_printoptions(legacy='1.25')

    if display == 'string':
        original_screen = sys.stdout
        diagram_html = io.StringIO()
        sys.stdout = diagram_html
    
    
    hsize = size[0] # horizontal size of graph
    vsize = size[1] # vertical size of graph
    
    lbor = bor[0] # left border (x-coordinate)
    rbor = bor[1] # right border (x-coordinate)
    bbor = bor[2] # bottom border (y-coordinate)
    tbor = bor[3] # top border (y-coordinate)
 
    indent = '  ' # indentation for html file
    
    # Introductory commands
    
    if display != 'string':
        print('Create an html file from the entire output or copy the script section into the Desmos console with Ctrl+Shift+J')
        print()
    
    print('<script src="https://www.desmos.com/api/v1.9/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>')
    
    s = '<div id="calculator" style="width: hsizepx; height: vsizepx;"></div>'
    s = s.replace('hsize',str(hsize))
    s = s.replace('vsize',str(vsize))
    print(s) # dimensions
    
    print('<script>') 
    
    print(indent + "var elt = document.getElementById('calculator');")
    print(indent + 'var Calc = Desmos.GraphingCalculator(elt);')
    print()
    
    # Expressions
    
    if exps != [[]]:
        lines = len(exps)
        for i in np.arange(lines):
            s0 = indent + 'Calc.setExpression({ id: "name", type: "expression", latex: "explatex", color: "hue" })'
            
            s = s0.replace('name',str(exps[i][0]))
            s = s.replace('explatex',str(exps[i][1]))
            s = s.replace('hue',str(exps[i][2]))
            print(s)
        print()
    
    # Blocks
       
    if blocks != [[]]:
        lines = len(blocks)
        for i in np.arange(lines):
            # Draw blocks as polygons
            
            s0 = indent + 'Calc.setExpression({ id:"name", type: "table", columns: [ { latex: "XX", values: xval }, { latex: "YY", values: yval, points: false } ] })'
            
            s = s0.replace('name',str(blocks[i][0]))
            s = s.replace('XX',str(blocks[i][1]))
            s = s.replace('YY',str(blocks[i][2]))
            
            s = s.replace('xval',np.array2string(np.array(blocks[i][3])[0,:],separator=", "))
            s = s.replace('yval',np.array2string(np.array(blocks[i][3])[1,:],separator=", "))
            print(s)
            
            s0 = indent + 'Calc.setExpression({ id:"blockname", latex:"\\\\operatorname{polygon}\\\\left("XX","YY"\\\\right)", color:"hue", fillOpacity: dense, lines:true })'
    
            s = s0.replace('blockname',str(blocks[i][0]) + 'polygon')
            s = s.replace('"XX"',str(blocks[i][1]))
            s = s.replace('"YY"',str(blocks[i][2]))
            s = s.replace('hue',str(blocks[i][4]))
            s = s.replace('dense',str(blocks[i][5]))
            print(s)       
        print()
        
    # Streams
        
    if streams != [[]]:
        lines = len(streams)
        for i in np.arange(lines):
            # Draw streams consisting of one or more segments
            
            s0 = indent + 'Calc.setExpression({ id:"name", latex:"coordinates", color:"hue", points:false, lines:true, lineWidth:thickness })'
            
            s = s0.replace('name',str(streams[i][0]))
            
            st = str(streams[i][1])
            st = st.replace('[[','[')
            st = st.replace(']]',']')
            s = s.replace('coordinates','(' + st + ')')
            
            s = s.replace('hue',str(streams[i][2]))
            s = s.replace('thickness',str(streams[i][3]))
            print(s)
            
            # Draw arrows if specified for particular streams
            
            if len(streams[i]) > 4: # an arrow direction is specified for a stream
                XY = np.array(streams[i][1]) # extract X and Y coordinates
                ydim = XY.shape[1] # y-dimension of coordinate matrix
                
                if streams[i][4] != '': # right arrow requested
                    xy = XY[:,ydim-1] # obtain last point; arrowhead is always drawn at this point
                    x0 = xy[0]; y0 = xy[1] # obtain x- and y-coordinates of this point
                    
                    if streams[i][4] == 'left':
                        xa = x0 + tip*math.cos(ang); ya = y0 + tip*math.sin(ang)
                        xb = x0 + tip*math.cos(ang); yb = y0 - tip*math.sin(ang)
                    elif streams[i][4] == 'right':
                        xa = x0 - tip*math.cos(ang); ya = y0 + tip*math.sin(ang)
                        xb = x0 - tip*math.cos(ang); yb = y0 - tip*math.sin(ang)
                    elif streams[i][4] == 'up':
                        xa = x0 + tipv*math.cos(angv); ya = y0 - tipv*math.sin(angv)
                        xb = x0 - tipv*math.cos(angv); yb = y0 - tipv*math.sin(angv) 
                    elif streams[i][4] == 'down':
                        xa = x0 + tipv*math.cos(angv); ya = y0 + tipv*math.sin(angv)
                        xb = x0 - tipv*math.cos(angv); yb = y0 + tipv*math.sin(angv)                    
                    
                    xyarr = [[xa,x0,xb],[ya,y0,yb]]
                    
                    s = s0.replace('name',str(streams[i][0]) + 'arr')
                    st = str(xyarr)
                    st = st.replace('[[','[')
                    st = st.replace(']]',']')
                    s = s.replace('coordinates','(' + st + ')')
                    
                    s = s.replace('hue',str(streams[i][2]))
                    s = s.replace('thickness',str(streams[i][3]))
                    print(s)
        print()
    
    # Labels
    
    if labels != [[]]:  
        lines = len(labels)
        for i in np.arange(lines):
            # Place labels
            
            s0 = indent + 'Calc.setExpression({ id:"name", latex:"coordinates", color:"hue", hidden:true, showLabel:true, labelOrientation:"direction", labelSize:font, label:"labeltext" })'
            
            s = s0.replace('name',str(labels[i][0]))
            
            st = str(labels[i][1])
            st = st.replace('[','')
            st = st.replace(']','')
            s = s.replace('coordinates','(' + st + ')')
            
            s = s.replace('hue',str(labels[i][3]))
            s = s.replace('font','"' + str(labels[i][4]) + '"')
            s = s.replace('direction',str(labels[i][5]))
            s = s.replace('labeltext',str(labels[i][2]))
            print(s)
            
        print()
        
    # Concluding commands
    
    s = indent + 'Calc.setMathBounds({ left: lbor, right: rbor, bottom: bbor, top: tbor })'
    s = s.replace('lbor',str(lbor))
    s = s.replace('rbor',str(rbor))
    s = s.replace('tbor',str(tbor))
    s = s.replace('bbor',str(bbor))
    print(s) # x and y ranges of graph
    
    print(indent + 'Calc.updateSettings({ showGrid: false, showXAxis: false, showYAxis: false, lockViewport: true, expressionsCollapsed: true })')
    print('</script>')
    
    if display == 'string':
        sys.stdout = original_screen
        return diagram_html
