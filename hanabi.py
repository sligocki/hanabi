import random

class Object:
  def __repr__(self):
    return repr(self.__dict__)

DEBUG = False

COLOR = "COLOR"
NUMBER = "NUMBER"

class Card(Object):
  def __init__(self, color, num):  # Note: num -1 from card game 1->0, 5->4
    self.attr = { COLOR: color, NUMBER: num }
    self.knows = { COLOR: False, NUMBER: False }

  def color(self):
    return self.attr[COLOR]
  def num(self):
    return self.attr[NUMBER]

PLAY = "PLAY"
DISCARD = "DISCARD"
HINT = "HINT"

PLAYING = "PLAYING"
GAME_OVER = "GAME_OVER"
LOST = "LOST"
ILLEGAL_MOVE = "ILLEGAL_MOVE"

class Hanabi(Object):
  def __init__(self, players):
    self.players = players
    self.hand_size = 5
    self.num_colors = 5
    self.num_distrib = [5, 2, 2, 2, 1]
    self.num_attr = { COLOR: self.num_colors, NUMBER: len(self.num_distrib) }

    self.deck = []
    for color in range(self.num_colors):
      for num, count in enumerate(self.num_distrib):
        for _ in range(count):
          self.deck.append(Card(color, num))
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

    self.last_hint = [None for _ in range(len(self.players))]

  def Check(self, val, message):
    if not val:
      self.mode = ILLEGAL_MOVE
      self.message = "Illegal move: " + message

  def Draw(self):
    if not self.deck:
      self.mode = GAME_OVER
    else:
      return self.deck.pop()

  def ReplaceCard(self, player_num, card_num):
    card = self.hands[player_num][card_num]
    # Remove this card, and place new card at end.
    del self.hands[player_num][card_num]
    self.hands[player_num].append(self.Draw())

    self.remaining[card.color()][card.num()] -= 1
    assert self.remaining[card.color()][card.num()] >= 0

    return card

  def Run(self):
    while True:
      for player_num, player in enumerate(self.players):
        action, x = player.Play(player_num, self)
        self.last_hint[player_num] = None  # Clear so it doesn't get seen twice.
        if DEBUG:
          print
          print "Hands:", self.hands
          print "Played:", self.next_card
          print "Remaining:", self.remaining
          print "Hints:", self.num_hint_tokens, "Errors:", self.num_error_tokens
          print
          print "Action:", player_num, action, x
        if action == PLAY:
          self.Play(player_num, x)
        elif action == DISCARD:
          self.Discard(player_num, x)
        elif action == HINT:
          other_player, attribute, value = x
          self.Hint(other_player, attribute, value)

        if self.mode != PLAYING:
          return self.mode, sum(self.next_card), self.message, self.num_hint_tokens, self.num_error_tokens

  def IsPlayable(self, card):
    return card.num() == self.next_card[card.color()]

  def Play(self, player_num, card_num):
    card = self.ReplaceCard(player_num, card_num)
    if self.IsPlayable(card):
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

    self.last_hint[player_num] = (attribute, value)  # TODO: Add which cards it applies to.

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
    print "# Playable"
    print state.next_card
    print "# Remaining"
    print state.remaining
    print "# Hint tokens = ", state.num_hint_tokens
    print "# Error tokens = ", state.num_error_tokens

    return input("Move:")

  COLORS = ["R", "G", "B", "W", "P"]
  def OtherCardStr(self, card):
    return str(card.num()) + self.COLORS[card.color()]
  def OtherHandStr(self, hand):
    return [self.OtherCardStr(card) for card in hand]

  def SelfCardStr(self, card):
    num = str(card.num()) if card.knows[NUMBER] else "?"
    color = self.COLORS[card.color()] if card.knows[COLOR] else "?"
    return num + color
  def SelfHandStr(self, hand):
    return [self.SelfCardStr(card) for card in hand]

class SimplePlayer(Player):
  def Play(self, player_num, state):
    # Play (or discard) a card if we know everything about it and it can be
    # played (or is no longer useful).
    for card_num, card in enumerate(state.hands[player_num]):
      if False not in card.knows.values():
        if state.IsPlayable(card):
          return PLAY, card_num
        elif card.num() < state.next_card[card.color()]:
          return DISCARD, card_num
    # Hint most info possible.
    if state.num_hint_tokens:
      max_score = 0
      best_hint = None
      for other_num in range(len(state.players)):
        if other_num != player_num:
          for attr in COLOR, NUMBER:
            for attr_val in range(state.num_attr[attr]):
              hint = other_num, attr, attr_val
              score = self.HintValue(state, hint)
              if score > max_score:
                max_score = score
                best_hint = hint
      if best_hint:
        return HINT, best_hint
    # Discard
    card_num = random.randrange(len(state.hands[player_num]))
    return DISCARD, card_num

  def HintValue(self, state, hint):
    player_num, attr, attr_val = hint
    score = 0
    for card in state.hands[player_num]:
      if card.attr[attr] == attr_val and not card.knows[attr]:
        score += 1  # Literally count the number of pieces of info transmitted.
    return score

class SignalPlayer(Player):
  def __init__(self, discard_num=3):
    self.discard_num = discard_num

  def Play(self, player_num, state):
    # If partner hinted us, play the indicated card.
    last_hint = state.last_hint[player_num]
    if last_hint:
      attribute, value = last_hint
      return PLAY, value

    # Else see if we can hint partner.
    if state.num_hint_tokens:
      for other_num in range(len(state.players)):
        if other_num != player_num:
          has_attr = [None for _ in range(5)]
          for card in state.hands[other_num]:
            has_attr[card.color()] = COLOR
            has_attr[card.num()] = NUMBER
          for card_num, card in enumerate(state.hands[other_num]):
            if state.IsPlayable(card) and has_attr[card_num] != None:
              return HINT, (other_num, has_attr[card_num], card_num)

    # Else discard. Originally I discarded oldest card, but it turns out that
    # discarding card #3 is 1 point better, not sure why.
    return DISCARD, self.discard_num

class DimaPlayer(Player):
  def __init__(self, discard_num=1):
    self.discard_num = discard_num

  def Play(self, player_num, state):
    # If partner hinted us, play the indicated card.
    last_hint = state.last_hint[player_num]
    if last_hint:
      attribute, value = last_hint
      for card_num, card in enumerate(state.hands[player_num]):
        if card.attr[attribute] == value:
          return PLAY, card_num

    # Else see if we can hint partner.
    if state.num_hint_tokens:
      for other_num in range(len(state.players)):
        if other_num != player_num:
          allow_color = [True] * 5
          allow_num   = [True] * 5
          for card in state.hands[other_num]:
            if state.IsPlayable(card):
              # If we can unambiguously hint, do so.
              if allow_color[card.color()]:
                return HINT, (other_num, COLOR, card.color())
              if allow_num[card.num()]:
                return HINT, (other_num, NUMBER, card.num())
            # Don't allow any further cards to use these attributes (or
            # partner will play the wrong card).
            allow_color[card.color()] = False
            allow_num[card.num()] = False

    # Else discard. Originally I discarded oldest card, but it turns out that
    # discarding card #1 is 0.5 point better, not sure why.
    return DISCARD, self.discard_num


def TestPlayer(player, iters):
  total_score = 0
  for _ in range(iters):
    game = Hanabi([player, player])
    score = game.Run()[1]
    total_score += score
  return float(total_score) / iters

# DEBUG=True
# game = Hanabi([DimaPlayer(), DimaPlayer()])
# print game.Run()

iters = 1000
print "Simple", TestPlayer(SimplePlayer(), iters)
print "Signal", TestPlayer(SignalPlayer(), iters)
for x in range(5):
  print "Dima", x, TestPlayer(DimaPlayer(x), iters)
