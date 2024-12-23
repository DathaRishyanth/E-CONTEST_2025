"""
Python interpreter for the esoteric language ><> (pronounced /ˈfɪʃ/).
Usage: ./fish.py --help
More information: http://esolangs.org/wiki/Fish
Requires python 2.7/3.2 or higher.
"""

import sys
import os
import time
import random
from collections import defaultdict
# inputpath = '/home/saiganesh/Desktop/E-Contest/E-Contest/app/evaluation/input/qn1/tc1.txt'

# constants
NCHARS = "0123456789abcdef"
ARITHMETIC = "+-*%"  # not division, as it requires special handling
COMPARISON = {"=": "==", "(": "<", ")": ">"}
DIRECTIONS = {">": (1, 0), "<": (-1, 0), "v": (0, 1), "^": (0, -1)}
MIRRORS = {
    "/": lambda x, y: (-y, -x),
    "\\": lambda x, y: (y, x),
    "|": lambda x, y: (-x, y),
    "_": lambda x, y: (x, -y),
    "#": lambda x, y: (-x, -y)
}


# class _Getch:
#     """
#     Provide cross-platform getch functionality. Shamelessly stolen from
#     http://code.activestate.com/recipes/134892/
#     """
#     def __init__(self):
#         try:
#             self._impl = _GetchWindows()
#         except ImportError:
#             self._impl = _GetchUnix()

#     def __call__(self): return self._impl()


# class _GetchUnix:
#     def __init__(self):
#         import tty, sys

#     def __call__(self):
#         import sys, tty, termios
#         fd = sys.stdin.fileno()
#         old_settings = termios.tcgetattr(fd)
#         try:
#             tty.setraw(sys.stdin.fileno())
#             ch = sys.stdin.read(1)
#         finally:
#             termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#         return ch


# class _GetchWindows:
#     def __init__(self):
#         import msvcrt

#     def __call__(self):
#         import msvcrt
#         return msvcrt.getch()
# getch = _Getch()


# def read_character():
#     """Read one character from stdin. Returns -1 when no input is available."""
#     # if sys.stdin.isatty():
#     #     # we're in console, read a character from the user
#     #     char = getch()
#     #     # check for ctrl-c (break)
#     #     if ord(char) == 3:
#     #         sys.stdout.write("^C")
#     #         sys.stdout.flush()
#     #         raise KeyboardInterrupt
#     #     else: return char
#     # else:
#     #     # input is redirected using pipes
#     #     char = sys.stdin.read(1)
#     #     # return -1 if there is no more input available
#     with open("input.txt", 'r') as f:
#         char = f.read()


#     return char if char != "" else -1


class Interpreter:
    """
    ><> "compiler" and interpreter.
    """

    def __init__(self, code, inputpath, outputpath, Q):
        """
        Initialize a new interpreter.
        Arguments:
            code -- the code to execute as a string
        """
        # check for hashbang in first line
        # lines = code.split("\n")
        lines = code
        if lines[0][:2] == "#!":
            code = "\n".join(lines[1:])

        # construct a 2D defaultdict to contain the code
        self._codebox = defaultdict(lambda: defaultdict(int))
        line_n = char_n = 0
        # for char in code:
        #     if char != "\n":
        #         self._codebox[line_n][char_n] = 0 if char == " " else ord(char)
        #         char_n += 1
        #     else:
        #         char_n = 0
        #         line_n += 1
        for l in lines:
            for char in l:
                if char != "\n":
                    self._codebox[line_n][char_n] = 0 if char == " " else ord(char)
                    char_n += 1
                else:
                    char_n = 0
                    line_n += 1

        self._position = [-1, 0]
        self._direction = DIRECTIONS[">"]

        # the register is initially empty
        self._register_stack = [None]
        # string mode is initially disabled
        self._string_mode = None
        # have we encountered a skip instruction?
        self._skip = False

        self._stack = []
        self._stack_stack = [self._stack]

        # is the last outputted character a newline?
        self._newline = None

    def move(self,inputpath, outputpath, Q):
        """
        Move one step in the execution process, and handle the instruction (if
        any) at the new position.
        """
        # move one step in the current direction
        self._position[0] += self._direction[0]
        self._position[1] += self._direction[1]

        # wrap around if we reach the borders of the codebox
        if self._position[1] > max(self._codebox.keys()):
            # if the current position is beyond the number of lines, wrap to
            # the top
            self._position[1] = 0
        elif self._position[1] < 0:
            # if we're above the top, move to the bottom
            self._position[1] = max(self._codebox.keys())

        if self._direction[0] == 1 and self._position[0] > max(self._codebox[self._position[1]].keys()):
            # wrap to the beginning if we are beyond the last character on a
            # line and moving rightwards
            self._position[0] = 0;
        elif self._position[0] < 0:
            # also wrap if we reach the left hand side
            self._position[0] = max(self._codebox[self._position[1]].keys())

        # execute the instruction found
        if not self._skip:
            instruction = int(self._codebox[self._position[1]][self._position[0]])
            # the current position might not be a valid character
            try:
                # use space if current cell is 0
                instruction = chr(instruction) if instruction > 0 else " "
            except:
                instruction = None
            try:
                self._handle_instruction(inputpath, outputpath, instruction)
                # Q.put("ANSWER WRITTEN")
            except StopExecution:
                raise
            except KeyboardInterrupt:
                # avoid catching as error
                raise KeyboardInterrupt
            except Exception as e:
                # Q.put("something smells fishy...")
                raise StopExecution("something smells fishy...")
            return instruction

        self._skip = False

    def _handle_instruction(self,inputpath, outputpath, instruction):
        """
        Execute an instruction.
        """
        if instruction == None:
            # error on invalid characters
            raise Exception

        # handle string mode
        if self._string_mode != None and self._string_mode != instruction:
            self._push(ord(instruction))
            return
        elif self._string_mode == instruction:
            self._string_mode = None
            return

        # instruction is one of ^v><, change direction
        if instruction in DIRECTIONS:
            self._direction = DIRECTIONS[instruction]

        # direction is a mirror, get new direction
        elif instruction in MIRRORS:
            self._direction = MIRRORS[instruction](*self._direction)

        # pick a random direction
        elif instruction == "x":
            self._direction = random.choice(list(DIRECTIONS.items()))[1]

        # portal; move IP to coordinates
        elif instruction == ".":
            y, x = self._pop(), self._pop()
            # IP cannot reach negative codebox
            if x < 0 or y < 0:
                raise Exception
            self._position = [x, y]

        # instruction is 0-9a-f, push corresponding hex value
        elif instruction in NCHARS:
            self._push(int(instruction, len(NCHARS)))

        # instruction is an arithmetic operator
        elif instruction in ARITHMETIC:
            a, b = self._pop(), self._pop()
            exec("self._push(b{}a)".format(instruction))

        # division
        elif instruction == ",":
            a, b = self._pop(), self._pop()
            # try converting them to floats for python 2 compability
            try:
                a, b = float(a), float(b)
            except OverflowError:
                pass
            self._push(b / a)

        # comparison operators
        elif instruction in COMPARISON:
            a, b = self._pop(), self._pop()
            exec("self._push(1 if b{}a else 0)".format(COMPARISON[instruction]))

        # turn on string mode
        elif instruction in "'\"":  # turn on string parsing
            self._string_mode = instruction

        # skip one command
        elif instruction == "!":
            self._skip = True

        # skip one command if popped value is 0
        elif instruction == "?":
            if not self._pop():
                self._skip = True

        # push length of stack
        elif instruction == "l":
            self._push(len(self._stack))

        # duplicate top of stack
        elif instruction == ":":
            self._push(self._stack[-1])

        # remove top of stack
        elif instruction == "~":
            self._pop()

        # swap top two values
        elif instruction == "$":
            a, b = self._pop(), self._pop()
            self._push(a)
            self._push(b)

        # swap top three values
        elif instruction == "@":
            a, b, c = self._pop(), self._pop(), self._pop()
            self._push(a)
            self._push(c)
            self._push(b)

        # put/get register
        elif instruction == "&":
            if self._register_stack[-1] == None:
                self._register_stack[-1] = self._pop()
            else:
                self._push(self._register_stack[-1])
                self._register_stack[-1] = None

        # reverse stack
        elif instruction == "r":
            self._stack.reverse()

        # right-shift stack
        elif instruction == "}":
            self._push(self._pop(), index=0)

        # left-shift stack
        elif instruction == "{":
            self._push(self._pop(index=0))

        # get value in codebox
        elif instruction == "g":
            x, y = self._pop(), self._pop()
            self._push(self._codebox[x][y])

        # set (put) value in codebox
        elif instruction == "p":
            x, y, z = self._pop(), self._pop(), self._pop()
            self._codebox[x][y] = z

        # pop and output as character
        elif instruction == "o":
            self._output(chr(int(self._pop())))

        # pop and output as number
        elif instruction == "n":
            # print(self._pop)
            n = self._pop()
            # print(n)
            # with open(outputpath, "w") as f:
            #     f.write(1)
                # f.close()

            # print('*')
            # print(f"Outputting number: {n}")
            # try outputting without the decimal point if possible
            self._output(outputpath ,int(n) if int(n) == n else n)
            # self._output(outputpath ,n)
            # print(output)

        # get one character from input and push it
        elif instruction == "i":
            i = self._input(inputpath)
            self._push(ord(i) if isinstance(i, str) else i)

        # pop x and create a new stack with x members moved from the old stack
        elif instruction == "[":
            count = int(self._pop())
            if count == 0:
                self._stack_stack[-1], new_stack = self._stack, []
            else:
                self._stack_stack[-1], new_stack = self._stack[:-count], self._stack[-count:]
            self._stack_stack.append(new_stack)
            self._stack = new_stack

            # create a new register for this stack
            self._register_stack.append(None)

        # remove current stack, moving its members to the previous stack.
        # if this is the last stack, a new, empty stack is pushed
        elif instruction == "]":
            old_stack = self._stack_stack.pop()
            if not len(self._stack_stack):
                self._stack_stack.append([])
            else:
                self._stack_stack[-1] += old_stack
            self._stack = self._stack_stack[-1]

            # register is dropped
            self._register_stack.pop()
            if not len(self._register_stack):
                self._register_stack.append(None)

        # the end
        elif instruction == ";":

            raise StopExecution()

        # space is NOP
        elif instruction == " ":
            pass

        # invalid instruction
        else:
            raise Exception("Invalid instruction", instruction)

    def _push(self, value, index=None):
        """
        Push a value to the current stack.
        Keyword arguments:
            index -- the index to push/insert to. (default: end of stack)
        """
        self._stack.insert(len(self._stack) if index == None else index, value)

    def _pop(self, index=None):
        """
        Pop and return a value from the current stack.
        Keyword arguments:
            index -- the index to pop from (default: end of stack)
        """
        # don't care about exceptions - they are handled at a higher level
        value = self._stack.pop(len(self._stack) - 1 if index == None else index)
        # convert to int where possible to avoid float overflow
        if value == int(value):
            value = int(value)
        # print(value)
        return value

    def _input(self, inputpath):
        """
        Return an inputted character.
        """
        # return read_character()
        # inputpath = 'input.txt'
        with open(inputpath, 'r') as f:
            char = f.read()
            char = int(char)
        return char if char != "" else -1

    def _output(self, outputpath, output):
        """
        Output a string without a newline appended.
        """
        # output = str(output)
        try:
            # self._newline = output.endswith("\n")
            with open(outputpath, "a") as f:  # Use "a" mode to append to the output file
                f.write(str(output))
        except Exception as e:
            print(f"Error writing output to {outputpath}: {e}")
        # with open(outputpath, 'r') as f:
        #     char = f.read()
        # print(char)
            # char = int(char)
        # print(output)
        # print(type(output))
        #     print(type(output))
        # print(output)
        # sys.stdout.write(output)
        # sys.stdout.flush()

    # def run(self):
    #     try:
    #         while True:
    #             # try:
    #             instr = self.move()
    #     except StopExecution as stop:
    #         # only print a newline if the script didn't
    #         newline = ("\n" if (not self._newline) and self._newline != None else "")
    #         sys.exit()


class StopExecution(Exception):
    """
    Exception raised when a script has finished execution.
    """

    def __init__(self, message=None):
        self.message = message


# if __name__ == "__main__":
# import argparse

# parser = argparse.ArgumentParser(description="""
# Execute a ><> script.
# Executing a script is as easy as:
#     %(prog)s <script file>
# You can also execute code directly using the -c/--code flag:
#     %(prog)s -c '1n23nn;'
#     > 132
# The -v and -s flags can be used to prepopulate the stack:
#     %(prog)s echo.fish -s "hello, world" -v 32 49 50 51 -s "456"
#     > hello, world 123456""", usage="""%(prog)s [-h] (<script file> | -c <code>) [<options>]""",
# formatter_class=argparse.RawDescriptionHelpFormatter)

# group = parser.add_argument_group("code")
# # group script file and --code together to only allow one
# code_group = group.add_mutually_exclusive_group(required=True)
# code_group.add_argument("script",
#                         type=argparse.FileType("r"),
#                         nargs="?",
#                         help=".fish file to execute")
# code_group.add_argument("-c", "--code",
#                         metavar="<code>",
#                         help="string of instructions to execute")

# options = parser.add_argument_group("options")
# options.add_argument("-s", "--string",
#                      action="append",
#                      metavar="<string>",
#                      dest="stack")
# options.add_argument("-v", "--value",
#                      type=float,
#                      nargs="+",
#                      action="append",
#                      metavar="<number>",
#                      dest="stack",
#                      help="push numbers or strings onto the stack before execution starts")
# options.add_argument("-t", "--tick",
#                      type=float,
#                      default=0.0,
#                      metavar="<seconds>",
#                      help="define a tick time, or a delay between the execution of each instruction")
# options.add_argument("-a", "--always-tick",
#                      action="store_true",
#                      default=False,
#                      dest="always_tick",
#                      help="make every instruction cause a tick (delay), even whitespace and skipped instructions")

# # parse arguments from sys.argv
# arguments = parser.parse_args()

# initialize an interpreter
# if arguments.script:
#     code = arguments.script.read()
#     arguments.script.close()
# else:
def run(code, inputpath, outputpath, Q):
    # with open(codepath, 'r') as f:
    #     code = f.readlines()

    # add supplied values to the interpreters stack
    # if arguments.stack:
    #     for x in arguments.stack:
    #         if isinstance(x, str):
    #             interpreter._stack += [float(ord(c)) for c in x]
    #         else:
    #             interpreter._stack += x
    interpreter = Interpreter(code, inputpath, outputpath, Q)
    try:
        while True:
            # try:
            instr = interpreter.move(inputpath, outputpath, Q)
            # print('*')
    except StopExecution as stop:
        # print("*")
        Q.put("ANSWER WRITTEN")
        # only print a newline if the script didn't

        newline = ("\n" if (not interpreter._newline) and interpreter._newline != None else "")
        sys.exit()

        # if instr and not instr == " " or arguments.always_tick:
        # if instr and not instr == " ":
        #     time.sleep()
    # except KeyboardInterrupt:
    #     # exit cleanly
#     #     parser.exit(message="\n")
# if __name__ == "__main__":
#     import multiprocessing as mp
#     import filecmp
#     Q = mp.Queue()
#     with open('/home/saiganesh/Desktop/E-Contest/E-Contest/app/code.txt', 'r') as f:
#         code = f.read()
#     outputpath = '/home/saiganesh/Desktop/E-Contest/E-Contest/app/output/output.txt'
#     run(code,inputpath,outputpath,Q)
#     with open(outputpath, 'r') as f:
#         output_content = f.read()
#     print("Output Content:")
#     print(output_content)
#
#     with open('/home/saiganesh/Desktop/E-Contest/E-Contest/app/evaluation/expected_output/qn1/output-1.txt', 'r') as f:
#         expected_content = f.read()
#     print("\nExpected Content:")
#     print(expected_content)
#
#     if filecmp.cmp(outputpath, '/home/saiganesh/Desktop/E-Contest/E-Contest/app/evaluation/expected_output/qn1/output-1.txt'):
#         print('*')
#     else:
#         print('*')


