# `cligames`

## Board games in your terminal
* Connect4 and Tic-tac-toe with a text-based interface.
* Playable computer opponent, implemented using the minimax algorithm (with alpha–beta pruning).
* Each board game can be played as human versus human, human versus computer or computer versus computer.

## Setup

#### Install via pip

```
$ pip install cligames
```

#### Build from source

```
$ git clone https://github.com/tombch/cligames.git
$ cd cligames/
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install .
```

## How to play

#### Connect4

To start a game of Connect4 against the computer, enter:
```
$ cligames connect4
A new game has started.
┌───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
└───┴───┴───┴───┴───┴───┴───┘
Player X - choose a move: 
```

To make a move, enter the column number you wish to make a move in:
```
Player X - choose a move: 3   
┌───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │ X │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
└───┴───┴───┴───┴───┴───┴───┘
Player X chose move 3.
Decision time: 2.556 seconds
Player O is choosing... 
┌───┬───┬───┬───┬───┬───┬───┐
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │   │   │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│   │   │ O │ X │   │   │   │
├───┼───┼───┼───┼───┼───┼───┤
│ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
└───┴───┴───┴───┴───┴───┴───┘
Player O chose move 2.
Decision time: 1.437 seconds
Player X - choose a move: 
```

#### Tic-tac-toe

To start a game of Tic-tac-toe against the computer, enter:
```
$ cligames tictactoe
A new game has started.
┌───┬───┬───┬───┐
│ 2 │   │   │   │
├───┼───┼───┼───┤
│ 1 │   │   │   │
├───┼───┼───┼───┤
│ 0 │   │   │   │
├───┼───┼───┼───┤
│   │ 0 │ 1 │ 2 │
└───┴───┴───┴───┘
Player X - choose a move: 
```

To make a move, enter the `(x, y)` coordinates of the position you wish to make a move in:
```
Player X - choose a move: (1, 1)
┌───┬───┬───┬───┐
│ 2 │   │   │   │
├───┼───┼───┼───┤
│ 1 │   │ X │   │
├───┼───┼───┼───┤
│ 0 │   │   │   │
├───┼───┼───┼───┤
│   │ 0 │ 1 │ 2 │
└───┴───┴───┴───┘
Player X chose move (1, 1).
Decision time: 1.567 seconds
Player O is choosing... 
┌───┬───┬───┬───┐
│ 2 │   │   │   │
├───┼───┼───┼───┤
│ 1 │   │ X │   │
├───┼───┼───┼───┤
│ 0 │ O │   │   │
├───┼───┼───┼───┤
│   │ 0 │ 1 │ 2 │
└───┴───┴───┴───┘
Player O chose move (0, 0).
Decision time: 0.02 seconds
Player X - choose a move: 
```
