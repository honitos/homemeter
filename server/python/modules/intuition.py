import curses
#import curses.textpad

class intuition:
    colorset = 0
    curses = None
    screen = None
    window = None
    width = None
    height = None
    ystatus = 0
  
    def __init__(self):
        self.curses = curses
        self.screen = curses.initscr()
        self.width = self.screen.getmaxyx()[1] - 1
        self.height = self.screen.getmaxyx()[0] - 1

        self.curses.noecho()
        self.curses.cbreak()
        self.screen.keypad(1)

        if self.curses.has_colors():
            self.curses.start_color()
            self.curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)
            self.curses.init_pair(2, curses.COLOR_BLACK,curses.COLOR_WHITE)
            self.curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
            self.curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_CYAN)
            self.curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_RED)
            self.curses.init_pair(6, curses.COLOR_GREEN,curses.COLOR_BLACK)
            self.curses.curs_set(0)

    def __del__(self):
        self.screen.keypad(0)
        #self.close()

    def close(self):
        self.curses.flash()
        self.curses.echo()
        self.curses.nocbreak()
        self.curses.endwin()

    def draw_screen(self):
        if self.curses.has_colors():
            self.screen.bkgd(self.curses.color_pair(self.colorset))

        self.screen.box()
        self.screen.addstr(1,2,"homeServer V0.1 - 2019 - honitos")
        # Trennlinie Titelzeile
        self.screen.hline(2,1,curses.ACS_HLINE,self.width - 1)
        self.screen.addch(2,0,curses.ACS_LTEE)
        self.screen.addch(2,self.width,curses.ACS_RTEE)
        # Trennlinie Statuszeile      
        self.ystatus = self.height - 3
        self.screen.hline(self.ystatus - 1,1,curses.ACS_HLINE, self.width - 1)
        self.screen.addch(self.ystatus - 1,0,curses.ACS_LTEE)
        self.screen.addch(self.ystatus - 1,self.width,curses.ACS_RTEE)     
        self.screen.addstr(self.ystatus - 1,1," Status: ")
        # Trennlinie Optionen
        self.screen.hline(self.height - 2,1,curses.ACS_HLINE, self.width - 1)
        self.screen.addch(self.height - 2,0,curses.ACS_LTEE)
        self.screen.addch(self.height - 2,self.width,curses.ACS_RTEE)     
        self.screen.addstr(self.height - 1,1,"[q] Quit")

        self.screen.move(self.ystatus,1)
        self.screen.refresh()


    def write_status(self,status="-"):
        try:
            self.screen.addstr(self.ystatus,1,status,self.curses.A_BOLD)
            self.screen.addnstr(" " * self.width,self.width - 3 - len(status))
            #elf.screen.refresh()
        except:
            raise

    def write_error(self,error=""):
        try:
            self.screen.addstr(self.ystatus,60,error,self.curses.A_BOLD)
            self.screen.addnstr(" " * self.width,self.width - 60 - len(error))
        except:
            raise
            
    def update_screen(self):
        self.height, self.width = self.screen.getmaxyx()
        self.height -= 1
        self.width -= 1
        self.screen.clear()
        self.draw_screen()

if __name__ == "__main__":
    screen = intuition()
    screen.draw_screen()

    try:
        while 1:
            a = screen.screen.getch()
            
            if a == ord('q'):
                break
            elif a == screen.curses.KEY_RESIZE:
                screen.update_screen()    

            elif a != 1:
                screen.write_status("keypressed, value = " + str(a))
                screen.colorset += 1
                if screen.colorset > 6: screen.colorset = 0
                screen.write_status("colorset is = %s" % screen.colorset)

                screen.update_screen()
                #screen.draw_window()
                screen.write_status("colorset is = %s" % screen.colorset)

            ywert = 50
            chartw = screen.width - 2
            charth = screen.height - 5
            chartx = 1
            charty = 10
            for c in range(10): #chartw):
                #vline(y, x, ch, n)
                cy = c
                screen.screen.vline(cy, chartx + c, curses.ACS_CKBOARD, charth-cy)
    except:
        raise
    finally:
        screen.close()
        print("End.")
        
    print("Cleaning up.")
    screen.close()
