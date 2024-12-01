def flat_list(l: list[any]) -> list[any]:
  return [item for sublist in l for item in sublist]