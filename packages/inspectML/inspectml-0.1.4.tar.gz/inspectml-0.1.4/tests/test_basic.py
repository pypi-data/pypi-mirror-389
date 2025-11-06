from inspectML.evaluation import classification

# Example usage
X = [[0, 1], [1, 0], [2, 1], [3, 2]]
labels = [0, 0, 1, 1]
print(classification.SIL(X, labels))
print(classification.ARI([0, 0, 1, 1], [0, 1, 1, 1]))
