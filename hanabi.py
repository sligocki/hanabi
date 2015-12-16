ATTRIBUTE_COLOR = 0
ATTRIBUTE_NUMBER = 1

class Card:
  def __init__(self, color, num):
    self.attr = [None, None]
    self.attr[ATTRIBUTE_COLOR] = color
    self.attr[ATTRIBUTE_NUMBER] = num  # Note: -1 from card game 1->0, 5->4
    self.knows = [False, False]

PLAY_ACTION = 0
DISCARD_ACTION = 1
HINT_ACTION = 2

class Hanabi:
  def __init__(self, players):
    self.players = players
    self.hand_size = 5
    self.num_colors = 5
    self.num_distrib = [5, 2, 2, 2, 1]

    self.deck = []
    for color in range(self.num_colors):
      for num, count in enumerate(self.num_distrib):
        self.deck += [Card(color, num)] * count
    random.shuffle(self.deck)

    # Top card played for each color
    self.played = [-1 for _ in range(self.num_colors)]

    # Remaining cards (not played nor discarded).
    self.remaining = [self.num_distrib[:] for x in range(self.num_colors)]

    self.hands = [[self.Draw() for _ in range(self.hand_size)] for _ in players]
    self.num_hint_tokens = 8  #?
    self.num_error_tokens = 3  #?

  def Draw(self):
    card = self.deck.pop()
    self.remaining[card.color][card.num] -= 1
    assert self.remaining[card.color][card.num] >= 0
    return card

  def ReplaceCard(self, player_num, card_num):
    card = self.hands[player_num][card_num]
    # TODO: Maybe re-arrange?
    self.hands[player_num][card_num] = self.Draw()
    return card

  def Run(players):
    while True:
      for player_num, player in enumerate(self.players):
        action, x = player.Play(player_num, self)
        if action == PLAY_ACTION:
          self.Play(player_num, x)
        elif action == DISCARD_ACTION:
          self.Discard(player_num, x)
        elif action == HINT_ACTION:
          other_player, attribute, value = x
          self.Hint(other_player, attribute, value)

        if self.num_error_tokens == 0:
          return 0  # Lost the game

  def Play(self, player_num, card_num):
    card = ReplaceCard(player_num, card_num)
    if card.num == self.played[card.color] + 1:
      # Success
      self.played[card.color] += 1
    else:
      # Mistake
      self.num_error_tokens -= 1

  def Discard(self, player_num, card_num):
    ReplaceCard(player_num, card_num)
    self.num_hint_tokens += 1

  def Hint(self, player_num, attribute, value):
    self.num_hint_tokens -= 1
    assert self.num_hint_tokens >= 0

    revealed_cards = False
    for card in self.hands[player_num]:
      if card.attr[attribute] == value:
        card.knows[attribute] = True
        revealed_card == True
    assert revealed_cards

class Player:
  def Play(self, player_num, state):
    pass

class HumanPlayer:
  def Play(self, player_num, state):
    print "# Other hands"
    for other_num in range(state.players):
      if other_num != player_num:
        print other_num, self.OtherHandStr(state.hands[other_num])
    print "# Your hand"
    print self.SelfHandStr(state.hands[player_num])

    return input("Move:")

  COLORS = ["R", "G", "B", "W", "P"]
  def OtherCardStr(self, card):
    return (str(card.attr[ATTRIBUTE_NUM]) +
            card.colors[card.attr[ATTRIBUTE_COLOR]])
  def OtherHandStr(self, hand):
    return [self.OtherCardStr(card) for card in hand]

  def SelfCardStr(self, card):
    num = str(card.attr[ATTRIBUTE_NUM]) if card.knows[ATTRIBUTE_NUM] else "?"
    color = (card.colors[card.attr[ATTRIBUTE_COLOR]]
             if card.knows[ATTRIBUTE_COLOR] else "?")
    return num + color
  def SelfHandStr(self, hand):
    return [self.SelfCardStr(card) for card in hand]
