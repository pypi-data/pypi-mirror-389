import numpy as np
import pandas as pd
from typing import Optional, Union, List


def make_contrasts(
        *args,
        contrasts: Optional[Union[List[str], str]] = None,
        levels: Union[pd.DataFrame, List[str], np.ndarray]
) -> np.ndarray:
    """
    Generate contrast matrix, supporting direct input of pandas DataFrame as the levels parameter

    Parameters:
        *args: Contrast expression strings (e.g., "groupD")
        contrasts: List of contrast expressions (alternative to *args)
        levels: Design matrix (can directly input pd.DataFrame) or list of column names

    Returns:
        Contrast matrix (np.ndarray)
    """
    # Process levels parameter: if it's a DataFrame, automatically extract column names
    if isinstance(levels, pd.DataFrame):
        level_names = levels.columns.tolist()  # Get column names from DataFrame
    elif isinstance(levels, (list, np.ndarray)):
        level_names = list(levels)  # Convert to list
    else:
        raise TypeError("levels must be a pd.DataFrame, list, or np.ndarray")

    # Process contrast expressions (combine *args and contrasts parameters)
    contrast_list = []
    if contrasts is not None:
        if isinstance(contrasts, str):
            contrast_list.append(contrasts)
        else:
            contrast_list.extend(contrasts)
    contrast_list.extend(args)

    if not contrast_list:
        raise ValueError("At least one contrast expression must be provided")

    # Create mapping from levels to indices (for building contrast matrix)
    level_to_idx = {level: i for i, level in enumerate(level_names)}
    n_levels = len(level_names)
    n_contrasts = len(contrast_list)

    # Initialize contrast matrix
    cm = np.zeros((n_levels, n_contrasts), dtype=np.float64)

    # Parse each contrast expression
    for j, expr in enumerate(contrast_list):
        # Create environment containing levels (for eval parsing)
        level_env = {level: np.zeros(n_levels) for level in level_names}
        for level in level_names:
            level_env[level][level_to_idx[level]] = 1.0

        try:
            # Parse expression and compute result
            result = eval(expr, level_env.copy())
            # Ensure result is a 2D column vector (fix dimension mismatch issue)
            if result.ndim == 1:
                result = result.reshape(-1, 1)
            cm[:, j] = result.flatten()  # Assign to contrast matrix
        except Exception as e:
            raise ValueError(f"Error parsing contrast expression '{expr}': {str(e)}")

    return cm
