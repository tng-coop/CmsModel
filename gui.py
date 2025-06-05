from data import seed_data
from models import Category, Content
from tree_gui import TreeGui

if __name__ == '__main__':
    categories: dict[str, Category] = {}
    contents: dict[str, Content] = {}
    seed_data(categories, contents)
    TreeGui(categories, contents).run()
