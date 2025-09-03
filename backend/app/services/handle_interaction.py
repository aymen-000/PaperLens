from typing import Literal, Dict
from enum import Enum 
from backend.app.services.db_service import update_user_preferences , get_db




class InteractionType(Enum):
    LIKE = 1.0
    DISLIKE = -0.5
    VIEW = 0.1
    BOOKMARK = 0.8
    SHARE = 0.6
    DELETE = -0.9 
    
    
def user_interaction(int_type: Literal["like", "dislike", "view", "bookmark", "share", "delete"]) -> float:
    mapping = {
        "like": InteractionType.LIKE,
        "dislike": InteractionType.DISLIKE,
        "view": InteractionType.VIEW,
        "bookmark": InteractionType.BOOKMARK,
        "share": InteractionType.SHARE,
        "delete": InteractionType.DELETE,
    }
    return mapping[int_type].value


def user_paper_interaction(
    paper: Dict[str, str],
    int_type: Literal["like", "dislike", "view", "bookmark", "share", "delete"]
) -> Dict[str, float]:
    """
    Returns category weight updates based on user interaction with a paper.
    
    Example:
    >>> user_paper_interaction(paper, "like")
    {"cs.AI": 1.0, "cs.LG": 1.0}
    """

    # Get the interaction weight (e.g., LIKE → 1.0, DISLIKE → -0.5)
    interaction_weight = user_interaction(int_type)

    # Collect all categories of the paper
    categories = set()
    if paper.get("primary_category"):
        categories.add(paper["primary_category"])
    if paper.get("categories"):
        categories.update(paper["categories"])

    category_weights = {cat: interaction_weight for cat in categories}

    return category_weights

def interac_with_paper(paper: Dict[str, str],
    int_type: Literal["like", "dislike", "view", "bookmark", "share", "delete"] , user_id:str) -> None : 
    category_weights = user_paper_interaction(paper , int_type) 
    with get_db() as db : 
        updated_weights = update_user_preferences(db , user_id , category_weights) 
    return updated_weights



