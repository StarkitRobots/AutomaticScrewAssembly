screewSize ={
    #diam, headDiam, headHeight,chamferDistance, cutAngle, FilletRadius
    'hex':
    {   
        'M2':   [2,     4,      1.4,    0.4,    30,     0.1],
        'M2.5': [2.5,   5,      1.7,    0.45,   30,     0.1],
        'M3':   [3,     5.5,    2,      0.5,    30,     0.1],
        'M4':   [4,     7,      2.8,    0.7,    30,     0.2],
        'M5':   [5,     8,      3.5,    0.8,    30,     0.2],
        'M6':   [6,     10,     4,      1,      30,     0.25],
        'M8':   [8,     13,     5.3,    1.25,   30,     0.4],
        'M10':  [10,    17,     6.4,    1.5,    30,     0.4],
        'M12':  [12,    19,     7.5,    1.75,   30,     0.6],
        'M16':  [16,    24,     10,     2,      30,     0.6],
        'M20':  [20,    30,     12.5,   2.5,    30,     0.8]
    },
    
    'rounded': 
    {
        'M2':   [2],
        'M2.5': [2.5],
        'M3':   [3,     5.5,    2.9,    2.1],
        'M4':   [4,     7,      3.6,    2.8],
        'M5':   [5,     8.5,    4.4,    3.5],
        'M6':   [6,     10,     5,1,    4.2],
        'M8':   [8,     13,     6.6,    5.6],
        'M10':  [10,    16,     8.1,    7],
        'M12':  [12,    17,     7.5,    ]
           
        
           
    },
    'flat':{
           
    },
    'socket':{
           
    }

}
for key,value in screewSize['hex'].items():
       print(key)
for key,value in screewSize['hex'].items():
       print(value)
