import random

ATTRIBUTE_COLOR = 0
ATTRIBUTE_NUMBER = 1

class Card:
  def __init__(self, color, num):  # Note: num -1 from card game 1->0, 5->4
    self.attr = { ATTRIBUTE_COLOR: color, ATTRIBUTE_NUMBER: num }
    self.knows = { ATTRIBUTE_COLOR: False, ATTRIBUTE_NUMBER: False }

  def color(self):
    return self.attr[ATTRIBUTE_COLOR]
  def num(self):
    return self.attr[ATTRIBUTE_NUMBER]

PLAY_ACTION = 0
DISCARD_ACTION = 1
HINT_ACTION = 2

PLAYING = "PLAYING"
GAME_OVER = "GAME_OVER"
LOST = "LOST"
ILLEGAL_MOVE = "ILLEGAL_MOVE"

class Hanabi:
  def __init__(self, players):
    self.players = players
    self.hand_size = 5
    self.num_colors = 5
    self.num_distrib = [5, 2, 2, 2, 1]
    self.num_attr = { ATTRIBUTE_COLOR: self.num_colors,
                      ATTRIBUTE_NUMBER: len(self.num_distrib) }

    self.deck = []
    for color in range(self.num_colors):
      for num, count in enumerate(self.num_distrib):
        self.deck += [Card(color, num)] * count
    random.shuffle(self.deck)

    # Next card playable for each color
    self.next_card = [0 for _ in range(self.num_colors)]

    # Remaining cards (not played nor discarded).
    self.remaining = [self.num_distrib[:] for x in range(self.num_colors)]

    self.hands = [[self.Draw() for _ in range(self.hand_size)] for _ in players]
    self.num_hint_tokens = 8  #?
    self.num_error_tokens = 3  #?

    self.mode = PLAYING
    self.message = None

  def Check(self, val, message):
    if not val:
      self.mode = ILLEGAL_MOVE
      self.message = "Illegal move: " + message

  def Draw(self):
    if not self.deck:
      self.mode = GAME_OVER
    else:
      card = self.deck.pop()
      self.remaining[card.color()][card.num()] -= 1
      assert self.remaining[card.color()][card.num()] >= 0
      return card

  def ReplaceCard(self, player_num, card_num):
    card = self.hands[player_num][card_num]
    # TODO: Maybe re-arrange?
    self.hands[player_num][card_num] = self.Draw()
    return card

  def Run(self):
    while True:
      for player_num, player in enumerate(self.players):
        action, x = player.Play(player_num, self)
        print "Action:", player_num, action, x
        if action == PLAY_ACTION:
          self.Play(player_num, x)
        elif action == DISCARD_ACTION:
          self.Discard(player_num, x)
        elif action == HINT_ACTION:
          other_player, attribute, value = x
          self.Hint(other_player, attribute, value)

        if self.mode != PLAYING:
          return self.mode, sum(self.next_card), self.message

  def Play(self, player_num, card_num):
    card = self.ReplaceCard(player_num, card_num)
    if card.num() == self.next_card[card.color()]:
      # Success
      self.next_card[card.color()] += 1
    else:
      # Mistake
      self.num_error_tokens -= 1
      if self.num_error_tokens == 0:
        self.mode = LOST
        self.message = "Lost: Too many errors."

  def Discard(self, player_num, card_num):
    self.ReplaceCard(player_num, card_num)
    self.num_hint_tokens += 1

  def Hint(self, player_num, attribute, value):
    self.num_hint_tokens -= 1
    self.Check(self.num_hint_tokens >= 0, "No hints left")

    revealed_cards = False
    for card in self.hands[player_num]:
      if card.attr[attribute] == value:
        card.knows[attribute] = True
        revealed_cards = True
    self.Check(revealed_cards, "Hint revealed no cards.")

    # TODO: Remember last hints.

class Player:
  def Play(self, player_num, state):
    pass

class HumanPlayer:
  def Play(self, player_num, state):
    print "# Other hands"
    for other_num in range(len(state.players)):
      if other_num != player_num:
        print other_num, self.OtherHandStr(state.hands[other_num])
    print "# Your hand"
    print self.SelfHandStr(state.hands[player_num])
    print "# Next cards"
    print state.next_card
    print "# Hint tokens = ", state.num_hint_tokens
    print "# Error tokens = ", state.num_error_tokens

    return input("Move:")

  COLORS = ["R", "G", "B", "W", "P"]
  def OtherCardStr(self, card):
    return str(card.num()) + self.COLORS[card.color()]
  def OtherHandStr(self, hand):
    return [self.OtherCardStr(card) for card in hand]

  def SelfCardStr(self, card):
    num = str(card.num()) if card.knows[ATTRIBUTE_NUMBER] else "?"
    color = self.COLORS[card.color()] if card.knows[ATTRIBUTE_COLOR] else "?"
    return num + color
  def SelfHandStr(self, hand):
    return [self.SelfCardStr(card) for card in hand]

class SimplePlayer(Player):
  def Play(self, player_num, state):
    # Play (or discard) a card if we know everything about it and it can be
    # played (or is no longer useful).
    for card_num, card in enumerate(state.hands[player_num]):
      if card.knows == [True, True]:
        if card.num() == state.next_card(card.color()):
          return PLAY_ACTION, card_num
        elif card.num() < state.next_card(card.color()):
          return DISCARD_ACTION, card_num
    # Hint most info possible.
    if state.num_hint_tokens:
      max_val = 0
      best_hint = None
      for other_num in range(len(state.players)):
        if other_num != player_num:
          for attr in ATTRIBUTE_COLOR, ATTRIBUTE_NUMBER:
            for attr_val in range(state.num_attr[attr]):
              hint = other_num, attr, attr_val
              val = self.HintValue(state, hint)
              if val > max_val:
                max_val = val
                best_hint = hint
      if best_hint:
        return HINT_ACTION, best_hint
    # Discard
    card_num = random.randrange(len(state.hands[player_num]))
    return DISCARD_ACTION, card_num

  def HintValue(self, state, hint):
    player_num, attr, attr_val = hint
    val = 0
    for card in state.hands[player_num]:
      if card.attr[attr] == attr_val and not card.knows[attr]:
        val += 1  # Literally count the number of pieces of info transmitted.
    return val

game = Hanabi([SimplePlayer(), SimplePlayer()])
print game.Run()
