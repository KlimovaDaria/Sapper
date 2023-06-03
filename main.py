import pygame as pg
import random
from os import path
from enum import Enum


COLS = 16
ROWS = 16
IMAGE_SIZE = 30
BOMBS = 40

GREY = (190, 190, 190)


class Box(Enum):
    ZERO = 0
    NUM1 = 1
    NUM2 = 2
    NUM3 = 3
    NUM4 = 4
    NUM5 = 5
    NUM6 = 6
    NUM7 = 7
    NUM8 = 8
    BOMB = 9
    OPENED = 10
    CLOSED = 11
    FLAGED = 12
    BOMBED = 13
    NOBOMB = 14

    def next_number_box(self):
        return Box(self.value + 1)


class GameState(Enum):
    PLAYED = 0
    BOMBED = 1
    WINNER = 2
    STARTED = 3


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def equals(self, coord):
        return self.x == coord.x and self.y == coord.y


class Ranges:
    __allCoords = []
    __size = Coord(0, 0)

    @staticmethod
    def set_size(x, y):
        Ranges.__size = Coord(x, y)
        for x in range(Ranges.__size.x):
            for y in range(Ranges.__size.y):
                Ranges.__allCoords.append(Coord(x, y))

    @staticmethod
    def get_size():
        return Ranges.__size

    @staticmethod
    def get_all_coords():
        return Ranges.__allCoords

    @staticmethod
    def in_range(coord):
        return (
            coord.x >= 0
            and coord.x < Ranges.__size.x
            and coord.y >= 0
            and coord.y < Ranges.__size.y
        )

    @staticmethod
    def get_random_coord():
        randX = random.randint(0, Ranges.__size.x - 1)
        randY = random.randint(0, Ranges.__size.y - 1)
        return Coord(randX, randY)

    @staticmethod
    def get_coords_around(coord):
        list = []
        for x in range(coord.x - 1, coord.x + 2):
            for y in range(coord.y - 1, coord.y + 2):
                around = Coord(x, y)
                if Ranges.in_range(around):
                    if not (coord.equals(around)):
                        list.append(around)
        return list


class Matrix:
    def __init__(self, default_box):
        self.matrix = self.__set_matrix(default_box)

    def __set_matrix(self, default_box):
        matrix = []
        for i in range(Ranges.get_size().x):
            row = []
            for i in range(Ranges.get_size().y):
                row.append(default_box)
            matrix.append(row)
        return matrix

    def set(self, coord, box):
        if Ranges.in_range(coord):
            self.matrix[coord.x][coord.y] = box

    def get(self, coord):
        if Ranges.in_range(coord):
            return self.matrix[coord.x][coord.y]
        else:
            return "ZERO"


class Game:
    def __init__(self, total_bombs):
        Ranges.set_size(COLS, ROWS)
        self.bomb = Bomb(total_bombs)
        self.flag = Flag()

    def get_box(self, coord):
        if self.flag.get(coord) == Box.OPENED:
            return self.bomb.get(coord)
        return self.flag.get(coord)

    def start(self):
        self.state = GameState.STARTED
        self.bomb.start(True, Coord(0,0))
        self.flag.start()

    def get_state(self):
        return self.state

    def press_left_button(self, coord):
        if self.game_over():
            return
        if self.state == GameState.STARTED:
            self.state = GameState.PLAYED
            self.bomb.start(False, coord)
        self.__open_box(coord)
        self.__check_winner()

    def __open_box(self, coord):
        match self.flag.get(coord).name:
            case 'FLAGED': return
            case 'OPENED': 
                self.set_opened_to_closed_boxes_around_number(coord) 
                return
            case 'CLOSED':
                match self.bomb.get(coord).name:
                    case 'ZERO': 
                        self.__open_boxes_around(coord)
                        return
                    case 'BOMB': 
                        self.__open_bombs(coord)
                        return
                    case _: self.flag.set_opened_to_box(coord)

    def __open_bombs(self, bomb_coord):
        self.state = GameState.BOMBED
        self.flag.set_bombed_to_box(bomb_coord)
        for coord in Ranges.get_all_coords():
            if self.bomb.get(coord) == Box.BOMB:
                self.flag.set_opened_to_closed_bomb_box(coord)
            else:
                self.flag.set_nobomb_to_flagged_safe_box(coord)

    def __open_boxes_around(self, coord):
        self.flag.set_opened_to_box(coord)
        for around in Ranges.get_coords_around(coord):
            self.__open_box(around)

    def press_right_button(self, coord):
        if self.game_over() or self.state != GameState.PLAYED:
            return
        self.flag.toggle_flagged_to_box(coord)

    def set_opened_to_closed_boxes_around_number(self, coord):
        if self.bomb.get(coord) != Box.BOMB:
            if (
                self.flag.get_count_of_flaged_boxes_around(coord)
                == self.bomb.get(coord).value
            ):
                for around in Ranges.get_coords_around(coord):
                    if self.flag.get(around) == Box.CLOSED:
                        self.__open_box(around)

    def __check_winner(self):
        if self.state == GameState.PLAYED:
            if self.flag.get_count_of_closed_boxes() == self.bomb.get_total_bombs():
                self.state = GameState.WINNER

    def game_over(self):
        if self.state == GameState.PLAYED or self.state == GameState.STARTED:
            return False
        self.start()
        return True


class Bomb:
    def __init__(self, total_bombs):
        self.total_bombs = total_bombs
        self.fix_bomb_count()

    def start(self, is_start, coord):
        self.matrix_bomb = Matrix(Box.ZERO)
        if not is_start:
            for i in range(self.total_bombs):
                self.place_bomb(coord)

    def place_bomb(self, _coord):
        while True:
            coord = Ranges.get_random_coord()
            if Box.BOMB == self.matrix_bomb.get(coord) or _coord.equals(coord):
                continue
            self.matrix_bomb.set(coord, Box.BOMB)
            self.inc_numbers_around_bomb(coord)
            break

    def get(self, coord):
        return self.matrix_bomb.get(coord)

    def inc_numbers_around_bomb(self, coord):
        list_around = Ranges.get_coords_around(coord)
        for a in list_around:
            if Box.BOMB != self.matrix_bomb.get(a):
                self.matrix_bomb.set(a, self.matrix_bomb.get(a).next_number_box())

    def fix_bomb_count(self):
        max_bombs = Ranges.get_size().x * Ranges.get_size().y / 2
        if self.total_bombs > max_bombs:
            self.total_bombs = int(max_bombs)

    def get_total_bombs(self):
        return self.total_bombs


class Flag:
    def __init__(self):
        pass

    def start(self):
        self.matrix_flag = Matrix(Box.CLOSED)
        self.count_of_closed_boxes = Ranges.get_size().x * Ranges.get_size().y

    def get(self, coord):
        return self.matrix_flag.get(coord)

    def set_opened_to_box(self, coord):
        self.matrix_flag.set(coord, Box.OPENED)
        self.count_of_closed_boxes = self.count_of_closed_boxes - 1

    def set_flagged_to_box(self, coord):
        self.matrix_flag.set(coord, Box.FLAGED)

    def toggle_flagged_to_box(self, coord):
        if self.matrix_flag.get(coord) == Box.FLAGED:
            self.set_closed_to_box(coord)
        elif self.matrix_flag.get(coord) == Box.CLOSED:
            self.set_flagged_to_box(coord)
        else:
            return

    def set_closed_to_box(self, coord):
        self.matrix_flag.set(coord, Box.CLOSED)

    def get_count_of_closed_boxes(self):
        return self.count_of_closed_boxes

    def set_bombed_to_box(self, coord):
        self.matrix_flag.set(coord, Box.BOMBED)

    def set_opened_to_closed_bomb_box(self, coord):
        if self.matrix_flag.get(coord) == Box.CLOSED:
            self.matrix_flag.set(coord, Box.OPENED)

    def set_nobomb_to_flagged_safe_box(self, coord):
        if self.matrix_flag.get(coord) == Box.FLAGED:
            self.matrix_flag.set(coord, Box.NOBOMB)

    def get_count_of_flaged_boxes_around(self, coord):
        count = 0
        for around in Ranges.get_coords_around(coord):
            if self.matrix_flag.get(around) == Box.FLAGED:
                count = count + 1
        return count


class Sapper:
    def __init__(self):
        pg.init()
        pg.mixer.init()
        self.__init_panel()
        self.clock = pg.time.Clock()
        self.running = True

    def __init_panel(self):
        self.font_name = pg.font.match_font("ARIAL")
        self.game = Game(BOMBS)
        self.game.start()
        self.allCoords = Ranges.get_all_coords()
        self.screen = pg.display.set_mode(
            (Ranges.get_size().x * IMAGE_SIZE, Ranges.get_size().y * IMAGE_SIZE)
        )
        pg.display.set_caption("Sapper")
        self.dir = path.dirname(__file__)
        self.img_dir = path.join(self.dir, "img")
        self.icon = pg.image.load(path.join(self.img_dir, "icon.png"))
        pg.display.set_icon(self.icon)
        self.screen.fill(GREY)
        self.draw_all_coords()

    def draw_all_coords(self):
        for coord in self.allCoords:
            x, y = int(coord.x), int(coord.y)
            image = pg.image.load(
                path.join(self.img_dir, "{}.png".format(self.game.get_box(coord).name))
            )

            image = pg.transform.scale(image, (IMAGE_SIZE,IMAGE_SIZE))
            rect = image.get_rect()
            coordX = x * IMAGE_SIZE
            rect.x = coordX
            coordy = y * IMAGE_SIZE
            rect.y = coordy
            self.screen.blit(image, rect)

    def new(self):
        self.run()

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.events()
            self.update()
            self.draw()

    def update(self):
        self.draw_all_coords()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                x, y = int(event.pos[0] / IMAGE_SIZE), int(event.pos[1] / IMAGE_SIZE)
                coord = Coord(x, y)
                if event.button == 1:
                    self.game.press_left_button(coord)
                elif event.button == 3:
                    self.game.press_right_button(coord)
                else:
                    self.game.start()

    def draw(self):
        #self.draw_text(self.get_message(), 22, (0, 0, 0), 50, 10)
        pg.display.flip()

    def get_message(self):
        if self.game.get_state() == GameState.PLAYED:
            return "Think twice"
        elif self.game.get_state() == GameState.BOMBED:
            return "You lose"
        elif self.game.get_state() == GameState.WINNER:
            return "You are a winner"

    def draw_text(self, text, size, color, x, y):
        font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        pass


s = Sapper()
s.show_start_screen()
while s.running:
    s.new()
    s.show_go_screen()

pg.quit()
