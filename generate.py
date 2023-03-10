import sys
from crossword import *

# Thank you god for helping me do this so fast! I love you god!


class CrosswordCreator:

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # loop over all the variables in the crossword
        for i in self.crossword.variables:
            # loop over all the words in the variables domain
            # create a copy of the set, because we can't delete a variable from a set while iterating on the set.
            set_words = set(self.domains[i])
            for j in set_words:
                # if the length of the word is not equal to the length of the variable
                if len(j) != i.length:
                    # remove that particular word from the variables domain.
                    self.domains[i].remove(j)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # make a copy of the self.domains of the variable x which needs to be consistent with y
        self_domain = set(self.domains[x])
        # make the revised variable
        revised = False
        # if the variables overlap then only we need to check these things right.
        overlap = self.crossword.overlaps[x, y]
        if overlap:
            for i in self_domain:
                # for every variable in domain of x, iterate over every variable in domain of y
                if not any([i[overlap[0]] == j[overlap[1]] for j in self.domains[y]]):  # if no variable in y's domain
                    # intersects with the variable in x's domain then remove that word from x's domain
                    self.domains[x].remove(i)
                    revised = True
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # if arcs list is not provided we will begin with list of all [(x, y) where x and y are different variables.]
        if not arcs:
            arcs = [(x, y) for x in self.crossword.variables for y in self.crossword.variables if x != y]

        # now begin ac3
        while arcs:  # while there are still variables in the arcs list
            # deque the list
            new_arc = arcs[0]
            del arcs[0]

            if self.revise(new_arc[0], new_arc[1]):
                # check if the domain of the first variable is empty
                if self.domains[new_arc[0]] == {}:
                    # problem can't be solved
                    return False

                for i in (self.crossword.neighbors(new_arc[0]) - {new_arc[1]}):
                    arcs.append((i, new_arc[0]))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # we just have to check if all the variables in the assignment dictionary have a value
        return all([var in assignment.keys() for var in self.crossword.variables])

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        # checks that the length of each word assigned to a variable is equal to the length of the variable.
        len_check = all([
            var.length == len(assignment[var]) for var in assignment.keys()
        ])

        # check if no variables overlap
        arcs = [(x, y) for x in assignment.keys() for y in assignment.keys() if x != y]
        for arc in arcs:
            overlap = self.crossword.overlaps[arc[0], arc[1]]
            if overlap:
                if not assignment[arc[0]][overlap[0]] != assignment[arc[1]][overlap[1]]:
                    return False
        return len_check

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        return self.domains[var]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned_variables = list(set(self.crossword.variables) - set(assignment.keys()))
        # apply the length heuristic
        unassigned_variables.sort(key=lambda l: len(self.domains[l]))
        # apply the degree heuristic
        unassigned_variables.sort(key=lambda m: len(self.crossword.neighbors(m)), reverse=True)
        return unassigned_variables[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for i in self.domains[var]:
            assignment[var] = i
            result = self.backtrack(assignment)
            if result:
                return result
            del assignment[var]
        return None


def main():
    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
