class Node:
    """
    Node of a binary tree
    """
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class Tree:
    """
    Binary tree utilities
    """

    @staticmethod
    def create_tree(values):
        """
        Create a binary tree from a list of values (level order)
        Returns the root node.
        """
        if not values:
            return None

        nodes = [Node(v) for v in values]

        for i in range(len(nodes)):
            left_index = 2*i + 1
            right_index = 2*i + 2
            if left_index < len(nodes):
                nodes[i].left = nodes[left_index]
            if right_index < len(nodes):
                nodes[i].right = nodes[right_index]

        return nodes[0]

    @staticmethod
    def inorder(root):
        """Inorder traversal of the binary tree"""
        if root is None:
            return []
        return Tree.inorder(root.left) + [root.value] + Tree.inorder(root.right)

    @staticmethod
    def preorder(root):
        """Preorder traversal of the binary tree"""
        if root is None:
            return []
        return [root.value] + Tree.preorder(root.left) + Tree.preorder(root.right)

    @staticmethod
    def postorder(root):
        """Postorder traversal of the binary tree"""
        if root is None:
            return []
        return Tree.postorder(root.left) + Tree.postorder(root.right) + [root.value]

    @staticmethod
    def height(root):
        """Returns the height of the tree"""
        if root is None:
            return 0
        return 1 + max(Tree.height(root.left), Tree.height(root.right))
