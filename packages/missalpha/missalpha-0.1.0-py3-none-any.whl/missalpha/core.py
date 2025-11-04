import pandas as pd
import numpy as np

'''
The tools for Cronbach's alpha
'''

import numpy as np
import itertools


def unknown_loc(scores_mat):
    # print(scores_mat)
    n_person, n_item = scores_mat.shape
    unknown_mat_to_list = np.zeros_like(scores_mat)
    unknown_list_to_mat = []
    count = 0

    for iter_person in range(n_person):
        for iter_item in range(n_item):
            if np.isnan(scores_mat[iter_person, iter_item]):
                unknown_mat_to_list[iter_person, iter_item] = count
                unknown_list_to_mat.append((iter_person, iter_item))
                count += 1
            else:
                unknown_mat_to_list[iter_person, iter_item] = -1
    # print(count)
    # print(unknown_mat_to_list)
    # print(unknown_list_to_mat)
    return count, unknown_mat_to_list, unknown_list_to_mat


def sigma_x(scores_mat, unknown_info):

    # print(scores_mat)
    # print("------------------")
    # print(unknown_info)
    # print("-------------")

    unknown_count, unknown_mat_to_list, unknown_list_to_mat = unknown_info

    n_person, n_item = scores_mat.shape
    column_sum = np.nansum(scores_mat, axis=0)

    A_mat = np.zeros((unknown_count, unknown_count))
    b_array = np.zeros(unknown_count)

    const = 2.0 / n_person / (n_person - 1)

    for num_iter_1 in range(unknown_count):
        for num_iter_2 in range(unknown_count):
            if num_iter_1 == num_iter_2:
                A_mat[num_iter_1, num_iter_1] = 2.0 / n_person
                b_array[num_iter_1] = -column_sum[
                    unknown_list_to_mat[num_iter_1][1]] * const
            else:
                A_mat[num_iter_1, num_iter_2] = -const if unknown_list_to_mat[
                    num_iter_1][1] == unknown_list_to_mat[num_iter_2][1] else 0

    c_scaler = 0
    for item_iter in range(n_item):
        scores_squared = np.power(scores_mat[:, item_iter], 2)
        c_scaler += (np.nansum(scores_squared) -
                     np.nansum(scores_mat[:, item_iter])**2 / n_person) / (
                         n_person - 1)

    # print(A_mat)
    # print(b_array)
    # print(c_scaler)

    return A_mat, b_array, c_scaler


def sigma_x_value(scores_mat, unknown_info, unknown_value):
    # print("-----------")
    # print(scores_mat)
    # print(unknown_info)
    # print(unknown_value)
    unknown_count, unknown_mat_to_list, unknown_list_to_mat = unknown_info
    assert unknown_count == len(unknown_value), 'Length does not match'

    scores_tmp = scores_mat.copy()

    for num_iter in range(unknown_count):
        scores_tmp[unknown_list_to_mat[num_iter]] = unknown_value[num_iter]

    n_person, n_item = scores_tmp.shape

    # print(np.sum(np.var(scores_tmp, axis=0)) * n_person / (n_person - 1))
    # print("-----------------------------")
    return np.sum(np.var(scores_tmp, axis=0)) * n_person / (n_person - 1)





def sigma_y(scores_mat, unknown_info):

    # print(scores_mat)
    # print(unknown_info)
    unknown_count, unknown_mat_to_list, unknown_list_to_mat = unknown_info

    n_person, n_item = scores_mat.shape
    row_sum = np.nansum(scores_mat, axis=1)
    mat_sum = np.nansum(row_sum)

    A_mat = np.zeros((unknown_count, unknown_count))
    b_array = np.zeros(unknown_count)

    const = 2.0 / n_person / (n_person - 1)

    for num_iter_1 in range(unknown_count):
        for num_iter_2 in range(unknown_count):
            if num_iter_1 == num_iter_2:
                A_mat[num_iter_1, num_iter_1] = 2.0 / n_person
                b_array[num_iter_1] = row_sum[unknown_list_to_mat[num_iter_1][
                    0]] * 2.0 / (n_person - 1) - mat_sum * const
            else:
                A_mat[num_iter_1,
                      num_iter_2] = 2.0 / n_person if unknown_list_to_mat[
                          num_iter_1][0] == unknown_list_to_mat[num_iter_2][
                              0] else -const

    c_scaler = 0
    scores_squared = np.power(row_sum, 2)
    c_scaler = (np.sum(scores_squared) -
                np.sum(row_sum)**2 / n_person) / (n_person - 1)

    # print(A_mat)
    # print(b_array)
    # print(c_scaler)
    return A_mat, b_array, c_scaler



def sigma_y_value(scores_mat, unknown_info, unknown_value):
    # print(scores_mat)
    # print(unknown_info)
    # print(unknown_value)
    unknown_count, unknown_mat_to_list, unknown_list_to_mat = unknown_info
    assert unknown_count == len(unknown_value), 'Length does not match'

    scores_tmp = scores_mat.copy()

    for num_iter in range(unknown_count):
        scores_tmp[unknown_list_to_mat[num_iter]] = unknown_value[num_iter]

    n_person, n_item = scores_tmp.shape
    # print(np.var(np.sum(scores_tmp, axis=1)) * n_person / (n_person - 1))
    return np.var(np.sum(scores_tmp, axis=1)) * n_person / (n_person - 1)


def compute_cronbach_alpha(scores_mat, unknown_info, unknown_value):

    n_item = scores_mat.shape[1]
    sig_x = sigma_x_value(scores_mat, unknown_info, unknown_value)
    sig_y = sigma_y_value(scores_mat, unknown_info, unknown_value)

    return (n_item / (n_item - 1.0)) * (1.0 - sig_x / sig_y)

# MARK: todo
def cronbach_alpha_rough(
        scores_mat,  # type: np.ndarray
        score_max,  # type: int
        num_try=1000,  # type: int
        int_only=False,  # type: bool
):  # type: (...) -> Tuple[float, float]
    '''
    Compute the smallest and largest possible alpha by random sampling

    Args:
        scores_mat: A person by test matrix of scores
        scores_max: The largest possible score
        num_try: Number of sampling
        int_only: A bool indicating whether only picking integer scores

    Returns:
        alpha_min: The smallest possible alpha
        alpha_max: The largest possible alpha
    '''
    unknown_info = unknown_loc(scores_mat)
    unknown_count = unknown_info[0]
    # print(score_max)
    alpha_all_zero = compute_cronbach_alpha(scores_mat, unknown_info,
                                            np.array([0] * unknown_count))
    alpha_all_max = compute_cronbach_alpha(
        scores_mat, unknown_info, np.array([score_max] * unknown_count))
    if alpha_all_zero < alpha_all_max:
        alpha_min, alpha_max = alpha_all_zero, alpha_all_max
    else:
        alpha_min, alpha_max = alpha_all_max, alpha_all_zero

    for num_iter in range(num_try):
        if int_only:
            alpha = compute_cronbach_alpha(
                scores_mat, unknown_info,
                np.random.randint(score_max + 1, size=unknown_count))
        else:
            alpha = compute_cronbach_alpha(
                scores_mat, unknown_info,
                np.random.rand(unknown_count) * float(score_max))
        if alpha < alpha_min:
            alpha_min = alpha
        if alpha > alpha_max:
            alpha_max = alpha

    return alpha_min, alpha_max


def cronbach_alpha_enum(
        scores_mat,  # type: np.ndarray
        score_max,  # type: int
):  # type: (...) -> Tuple[float, float]
    '''
    Compute the smallest and largest possible alpha by enumerating

    Args:
        scores_mat: A person by test matrix of scores
        scores_max: The largest possible score

    Returns:
        alpha_min: The smallest possible alpha
        alpha_max: The largest possible alpha
    '''
    unknown_info = unknown_loc(scores_mat)
    unknown_count = unknown_info[0]

    alpha_min, alpha_max = 100.0, -100.0
    for scores in list(
            map(list,
                itertools.product(range(score_max + 1),
                                  repeat=unknown_count))):
        alpha = compute_cronbach_alpha(scores_mat, unknown_info,
                                       np.array(scores))
        if alpha < alpha_min:
            alpha_min = alpha
        if alpha > alpha_max:
            alpha_max = alpha

    return alpha_min, alpha_max


def generate_scores_mat_bernoulli(
        n_person,  # type: int
        n_item,  # type: int
        n_missing,  # type: int
        score_max=1,  # type: int
):  # type: (...) -> np.ndarray
    '''
    Generate a random person by test matrix of scores.
    The procedure is as followed:
    1. For each person, generate the ability in [0, 1) for him/her
        following iid uniform distribution
    2. Then for each test, generate the score on the test following
        iid binomial distribution with number = score_max, prob = ability
    Also, we randomly pick n_missing scores and mask it as np.nan

    Args:
        n_person: The number of all people
        n_item: The number of all test (or item)
        n_missing: The number of missing results (or scores)
        score_max: The largest possible score

    Returns:
        scores_mat: A person by test matrix of scores 
    '''
    scores_mat = np.zeros((n_person, n_item))
    scores_person = np.random.rand(n_person)
    missing_count = np.random.choice(n_person * n_item,
                                     n_missing,
                                     replace=False)

    for count, loc in enumerate(
            itertools.product(range(n_person), range(n_item))):
        if count in missing_count:
            scores_mat[loc] = np.nan
        else:
            scores_mat[loc] = np.random.binomial(score_max,
                                                 scores_person[loc[0]])

    return scores_mat



'''
The tools for Cronbach's alpha
'''

import numpy as np
import cvxpy as cvx
import qcqp


def qp_solver(
        n,  # type: int
        A,  # type: np.ndarray
        b,  # type: np.ndarray
        c,  # type: float
        x_max=1,  # type: int
        print_message=False,  # type: bool
):  # type: (...) -> Tuple[float, np.ndarray]
    '''
    The function for sloving (nonconvex) quadratic programming
    The objective is min 1/2 * x^T A x + b^T x + c

    Args:
        n: Dimension of the problem
        A: An n x n numpy array, quadratic term
        b: An n X 1 numpy array, linear term
        c: A float, constant term
        x_max: An integer indicating the largest possible score
        print_message: A bool indicating whether print
            the objective and violation
    '''

    # print(        n,  # type: int
    #     A,  # type: np.ndarray
    #     b,  # type: np.ndarray
    #     c,  # type: float
    #     x_max,  # type: int
    #     )
    # raise Exception("Xxxxxxxxxx")
    # Form a nonconvex problem.
    x = cvx.Variable(n)
    obj = (1 / 2) * cvx.quad_form(x, A) + b.T @ x + c
    cons = [0.0 <= x, x <= float(x_max)]
    prob = cvx.Problem(cvx.Minimize(obj), cons)

    # Create a QCQP handler.
    qcqp_handler = qcqp.QCQP(prob)

    # Get a starting point
    qcqp_handler.suggest(qcqp.RANDOM)

    # Attempt to improve the starting point given by the suggest method
    f_cd, v_cd = qcqp_handler.improve(qcqp.COORD_DESCENT)
    if print_message:
        print("Coordinate descent: objective %.3f, violation %.3f" %
              (f_cd, v_cd))
        print(x.value)

    return f_cd, x.value


def examine_alpha_bound(
        alpha,  # type: float
        n_item,  # type: int
        sigma_x_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        sigma_y_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        alpha_type,  # type: Literal['min', 'max']
        score_max=1,  # type: int
        num_try=1,  # type: int
):  # type: (...) -> Tuple[bool, Optional[np.ndarray]]
    '''
    The function to check whether alpha is a feasible solution to
        min/max problem

    Args:
        alpha: The value of alpha we want to check
        n_item: The number of all items
        sigma_x_info: The info in quadratic function of sigma_x
        sigma_y_info: The info in quadratic function of sigma_y
        alpha_type: Whether we want to check the min or max problem
        score_max: The largest possible score
        num_try: The number of optmization algorithms we run

    Returns:
        result: A bool indicating whether alpha is feasible
        x_value: The optimal solution
    '''

    # print(
    #     alpha,  # type: float
    #     n_person,  # type: int
    #     sigma_x_info,  # type: Tuple[np.ndarray, np.ndaray, float]
    #     sigma_y_info,  # type: Tuple[np.ndarray, np.ndaray, float]
    #     alpha_type,  # type: Literal['min', 'max']
    #     score_max,  # type: int
    #     num_try  # type: int
    # )
    # raise Exception("Xxxxxxxxxx")
    if alpha_type == 'min':
        const_x, const_y = -1.0, 1.0 - alpha * (n_item - 1.0) / n_item
    elif alpha_type == 'max':
        const_x, const_y = 1.0, -1.0 + alpha * (n_item - 1.0) / n_item
    else:
        raise Exception('alpha_type can only be "min" or "max"')

    A_mat_x, b_array_x, c_scaler_x = sigma_x_info
    A_mat_y, b_array_y, c_scaler_y = sigma_y_info

    A_mat = const_x * A_mat_x + const_y * A_mat_y
    b_array = const_x * b_array_x + const_y * b_array_y
    c_scaler = const_x * c_scaler_x + const_y * c_scaler_y

    for num_iter in range(num_try):
        opt_value, x_value = qp_solver(len(b_array),
                                       A_mat,
                                       b_array,
                                       c_scaler,
                                       x_max=score_max)
        if opt_value <= 0:
            return True, np.array(x_value).T[0]

    return False, None


def compute_alpha_min(
        n_item,  # type: int
        sigma_x_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        sigma_y_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        score_max=1,  # type: int
        alpha_lb=0.0,  # type: float
        alpha_ub=1.0,  # type: float
        tol=1e-3,  # type: float
        num_try=1,  # type: int
):  # type: (...) -> float

    '''
    The function to compute the smallest poosible alpha

    Args:
        n_item: The number of all items
        sigma_x_info: The info in quadratic function of sigma_x
        sigma_y_info: The info in quadratic function of sigma_y
        score_max: The largest possible score
        alpha_lb: A lower bound of alpha, usually 0.0
        alpha_ub: An upper bound of alpha, usually 1.0
        tol: The desired accuracy of lower and upper bound of alpha
        num_try: The number of optmization algorithms we run

    Returns:
        ans: The smallest possible alpha
    '''

#     print(
#     n_person,  # type: int
#     sigma_x_info,  # type: Tuple[np.ndarray, np.ndaray, float]
#     sigma_y_info,  # type: Tuple[np.ndarray, np.ndaray, float]
#     score_max,  # type: int
#     alpha_lb, # type: float
#     alpha_ub,  # type: float
#     tol,  # type: float
#     num_try  # type: int
# )
#     raise Exception("Xxxxxxxxxx")
    lb, ub = alpha_lb + 0.0, alpha_ub + 0.0

    while ub - lb > tol:
        alpha_mid = (ub + lb) / 2
        result, _ = examine_alpha_bound(alpha_mid,
                                        n_item,
                                        sigma_x_info,
                                        sigma_y_info,
                                        'min',
                                        score_max=score_max,
                                        num_try=num_try)
        if result:
            ub = alpha_mid
        else:
            lb = alpha_mid

    return (lb + ub) / 2


def compute_alpha_max(
        n_item,  # type: int
        sigma_x_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        sigma_y_info,  # type: Tuple[np.ndarray, np.ndaray, float]
        score_max=1,  # type: int
        alpha_lb=0.0,  # type: float
        alpha_ub=1.0,  # type: float
        tol=1e-3,  # type: float
        num_try=1,  # type: int
):  # type: (...) -> float
    '''
    The function to compute the largest poosible alpha

    Args:
        n_item: The number of all items
        sigma_x_info: The info in quadratic function of sigma_x
        sigma_y_info: The info in quadratic function of sigma_y
        score_max: The largest possible score
        alpha_lb: A lower bound of alpha, usually 0.0
        alpha_ub: An upper bound of alpha, usually 1.0
        tol: The desired accuracy of lower and upper bound of alpha
        num_try: The number of optmization algorithms we run

    Returns:
        ans: The largest possible alpha
    '''
    lb, ub = alpha_lb + 0.0, alpha_ub + 0.0

    while ub - lb > tol:
        alpha_mid = (ub + lb) / 2
        result, _ = examine_alpha_bound(alpha_mid,
                                        n_item,
                                        sigma_x_info,
                                        sigma_y_info,
                                        'max',
                                        score_max=score_max,
                                        num_try=num_try)
        if result:
            lb = alpha_mid
        else:
            ub = alpha_mid

    return (lb + ub) / 2


"""
The tools for Cronbach's alpha
"""

import time
from typing import Tuple
import logging
from warnings import filterwarnings

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def cronbachs_alpha(
    scores_mat: np.ndarray,
    score_max: int,
    tol: float = 1e-3,
    num_random: int = 1000,
    enum_all: bool = False,
    num_opt: int = 1,
    debug: bool = True,
) -> Tuple[float, float]:
    """
    Main function in computing lower and upper bound of Cronbach's alpha.

    Args:
        scores_mat: A person by test (or item) numpy array provides
            the performance of a person on a test,
            np.nan if the result is missing
        score_max: An integer indicating the largest possible score of the test
        tol: The desired accuracy in the lower and upper bound
        num_random: An integer indicating the number of random sampling
            in estimating the lower and upper bound
        enum_all: A bool indicating whether enumerate all possible scores
        num_opt: An integer indicating the number we run the optimization algorithm

    Returns:
        alpha_min_opt: The smallest possible alpha given by the optimization algorithm
        alpha_max_opt: The largest possible alpha given by the optimization algorithm
    """
    filterwarnings("ignore", category=FutureWarning)
    if debug:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    t = time.time()

    alpha_min_sample_int, alpha_max_sample_int = cronbach_alpha_rough(
        scores_mat, score_max, num_try=num_random, int_only=True
    )
    logger.debug("-" * 30)
    logger.debug(
        "Elasped time in random sampling (integer only): %.2f" % (time.time() - t)
    )
    logger.debug(
        "alpha_min: %.4f, alpha_max: %.4f"
        % (alpha_min_sample_int, alpha_max_sample_int)
    )
    logger.debug("-" * 30)

    t = time.time()

    alpha_min_sample, alpha_max_sample = cronbach_alpha_rough(
        scores_mat, score_max, num_try=num_random, int_only=False
    )
    logger.debug(
        "Elasped time in random sampling (float allowed): %.2f" % (time.time() - t)
    )
    logger.debug(
        "alpha_min: %.4f, alpha_max: %.4f" % (alpha_min_sample, alpha_max_sample)
    )
    logger.debug("-" * 30)

    if enum_all:
        t = time.time()
        alpha_min_enum, alpha_max_enum = cronbach_alpha_enum(
            scores_mat, score_max
        )
        logger.debug("Elasped time in enumerating: %.2f" % (time.time() - t))
        logger.debug(
            "alpha_min: %.4f, alpha_max: %.4f" % (alpha_min_enum, alpha_max_enum)
        )
        logger.debug("-" * 30)

    t = time.time()

    unknown_info = unknown_loc(scores_mat)
    sigma_x_info = sigma_x(scores_mat, unknown_info)
    sigma_y_info = sigma_y(scores_mat, unknown_info)

    alpha_min_opt = compute_alpha_min(
        scores_mat.shape[1],
        sigma_x_info,
        sigma_y_info,
        score_max=score_max,
        num_try=num_opt,
    )
    alpha_max_opt = compute_alpha_max(
        scores_mat.shape[1],
        sigma_x_info,
        sigma_y_info,
        score_max=score_max,
        num_try=num_opt,
    )
    logger.debug("Elasped time in optimization: %.2f" % (time.time() - t))
    logger.debug("alpha_min: %.4f, alpha_max: %.4f" % (alpha_min_opt, alpha_max_opt))
    logger.debug("-" * 30)

    return alpha_min_opt, alpha_max_opt




# scores_df = pd.read_csv("sample.csv")
# scores_mat = scores_df.to_numpy()
# # print(scores_mat)
# alpha_min_opt, alpha_max_opt = cronbachs_alpha(scores_mat, 4, enum_all=False)
# alpha_min_opt, alpha_max_opt = cronbachs_alpha(scores_mat, 4, enum_all=True)

score_max = 2
scores_mat_bernoulli = generate_scores_mat_bernoulli(
    50, 10, 20, score_max
)
# # print(scores_mat_bernoulli)
alpha_min_opt, alpha_max_opt = cronbachs_alpha(
    scores_mat_bernoulli, score_max, enum_all=False
)