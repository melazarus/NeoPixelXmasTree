class animation_type:
    none = "none"
    scroll = "scroll"
    sparkle = "sparkle"
    swirl = "swirl"
    
class animation_speed:
    fast = .1
    slow = .3
    
#column mapping for this tree, must be updated to match other trees individually
octants = [None]*8
octants[0] = {0,12,27,31,40,48,49}
octants[1] = {1,7,13,18,23,35,38}
octants[2] = {2,8,28,32}
octants[3] = {14,19,24,41,43}
octants[4] = {3,9,15,20,29,36,39,46,47}
octants[5] = {4,10,25,33,45}
octants[6] = {5,11,16,21,26,30,37}
octants[7] = {6,17,22,34,42,44}