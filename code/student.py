import numpy as np
import cv2
import random
import matplotlib.pyplot as plt

def calculate_projection_matrix(image, markers):
    """
    To solve for the projection matrix. You need to set up a system of
    equations using the corresponding 2D and 3D points. See the handout, Q5
    of the written questions, or the lecture slides for how to set up these
    equations.

    Don't forget to set M_34 = 1 in this system to fix the scale.

    :param image: a single image in our camera system
    :param markers: dictionary of markerID to 4x3 array containing 3D points
    
    :return: M, the camera projection matrix which maps 3D world coordinates
    of provided aruco markers to image coordinates
             residual, the error in the estimation of M given the point sets
    """
    ######################
    # Do not change this #
    ######################

    # Markers is a dictionary mapping a marker ID to a 4x3 array
    # containing the 3d points for each of the 4 corners of the
    # marker in our scanning setup
    dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_1000)
    parameters = cv2.aruco.DetectorParameters_create()

    markerCorners, markerIds, rejectedCandidates = cv2.aruco.detectMarkers(
        image, dictionary, parameters=parameters)
    markerIds = [m[0] for m in markerIds]
    markerCorners = [m[0] for m in markerCorners]

    points2d = []
    points3d = []

    for markerId, marker in zip(markerIds, markerCorners):
        if markerId in markers:
            for j, corner in enumerate(marker):
                points2d.append(corner)
                points3d.append(markers[markerId][j])

    points2d = np.array(points2d)
    points3d = np.array(points3d)

    ########################
    # TODO: Your code here #
    ########################
    # # Placeholder values. This M matrix came from a call to rand(3,4). It leads to a high residual.
    print('Randomly setting matrix entries as a placeholder')
    M = np.array([[0.1768, 0.7018, 0.7948, 0.4613],
                  [0.6750, 0.3152, 0.1136, 0.0480],
                  [0.1020, 0.1725, 0.7244, 0.9932]])
    residual = 7 # Arbitrary stencil code initial value placeholder

    # construct matrix A
    A = np.zeros((np.size(points2d), 11))
    for i in range(points2d.shape[0]):
        ui, vi = points2d[i, 0], points2d[i, 1]
        Xi, Yi, Zi = points3d[i, 0], points3d[i, 1], points3d[i, 2]
        A1 = np.array([Xi, Yi, Zi, 1, 0, 0, 0, 0, -Xi*ui, -Yi*ui, -Zi*ui])
        A[i*2, :] = A1
        A2 = np.array([0, 0, 0, 0, Xi, Yi, Zi, 1, -Xi*vi, -Yi*vi, -Zi*vi])
        A[i*2+1, :] = A2

    # construct matrix b, a list of 2d points
    b = points2d.flatten().T

    # using least square to solve for M
    lstsq = np.linalg.lstsq(A, b)

    # get M and residual
    M_temp = lstsq[0]
    residual = lstsq[1]

    M = np.append(M_temp, 1).reshape((3, 4))

    return M, residual

def normalize_coordinates(points):
    """
    ============================ EXTRA CREDIT ============================
    Normalize the given Points before computing the fundamental matrix. You
    should perform the normalization to make the mean of the points 0
    and the average magnitude 1.0.

    The transformation matrix T is the product of the scale and offset matrices.

    Offset Matrix
    Find c_u and c_v and create a matrix of the form in the handout for T_offset

    Scale Matrix
    Subtract the means of the u and v coordinates, then take the reciprocal of
    their standard deviation i.e. 1 / np.std([...]). Then construct the scale
    matrix in the form provided in the handout for T_scale

    :param points: set of [n x 2] 2D points
    :return: a tuple of (normalized_points, T) where T is the [3 x 3] transformation
    matrix
    """
    ########################
    # TODO: Your code here #
    ########################
    # This is a placeholder with the identity matrix for T replace with the
    # real transformation matrix for this set of points
    T = np.eye(3)

    return points, T

def estimate_fundamental_matrix(points1, points2):
    """
    Estimates the fundamental matrix given set of point correspondences in
    points1 and points2. The fundamental matrix will transform a point into 
    a line within the second image - the epipolar line - such that F x' = l. 
    Fitting a fundamental matrix to a set of points will try to minimize the 
    error of all points x to their respective epipolar lines transformed 
    from x'. The residual can be computed as the difference from the known 
    geometric constraint that x^T F x' = 0.

    points1 is an [n x 2] matrix of 2D coordinate of points on Image A
    points2 is an [n x 2] matrix of 2D coordinate of points on Image B

    Implement this function efficiently as it will be
    called repeatedly within the RANSAC part of the project.

    If you normalize your coordinates for extra credit, don't forget to adjust
    your fundamental matrix so that it can operate on the original pixel
    coordinates!

    :return F_matrix, the [3 x 3] fundamental matrix
            residual, the error in the estimation
    """
    ########################
    # TODO: Your code here #
    ########################

    # Arbitrary intentionally incorrect Fundamental matrix placeholder
    F_matrix = np.array([[0, 0, -.0004], [0, 0, .0032], [0, -0.0044, .1034]])
    residual = 5 # Arbitrary stencil code initial value placeholder

    # construct matrix A on the left side
    A = np.zeros((points1.shape[0], 9))
    for i in range(points1.shape[0]):
        u1, v1 = points1[i, 0], points1[i, 1]
        u2, v2 = points2[i, 0], points2[i, 1]
        A[i, :] = [u1*u2, v1*u2, u2, u1*v2, v1*v2, v2, u1, v1, 1]
    
    # decompose A using SVD and get F_matrix
    u, s, vh = np.linalg.svd(A)
    idx = np.argmin(s)
    F = vh[idx, :]
    F_matrix = np.reshape(F, (3, 3))

    # correct F
    u, s, vh = np.linalg.svd(F_matrix)
    idx = np.argmin(s)
    s[idx] = 0
    s = np.diag(s)
    F_matrix = u @ s @ vh

    # calculate residual
    errors = []
    points1_homo = np.hstack((points1, np.ones((points1.shape[0], 1))))
    points2_homo = np.hstack((points2, np.ones((points2.shape[0], 1))))
    for p1, p2 in zip(points1_homo, points2_homo):
        output = p1 @ F_matrix @ p2.T
        errors.append(output**2)
    residual = np.sqrt(np.sum(errors))

    return F_matrix, residual

def ransac_fundamental_matrix(matches1, matches2, num_iters):
    """
    Implement RANSAC to find the best fundamental matrix robustly
    by randomly sampling interest points.
    
    Inputs:
    matches1 and matches2 are the [N x 2] coordinates of the possibly
    matching points across two images. Each row is a correspondence
     (e.g. row 42 of matches1 is a point that corresponds to row 42 of matches2)

    Outputs:
    best_Fmatrix is the [3 x 3] fundamental matrix
    best_inliers1 and best_inliers2 are the [M x 2] subset of matches1 and matches2 that
    are inliners with respect to best_Fmatrix
    best_inlier_residual is the error induced by best_Fmatrix

    :return: best_Fmatrix, inliers1, inliers2, best_inlier_residual
    """
    # DO NOT TOUCH THE FOLLOWING LINES
    random.seed(0)
    np.random.seed(0)
    
    ########################
    # TODO: Your code here #
    ########################

    # Your RANSAC loop should contain a call to your 'estimate_fundamental_matrix()'

    # Placeholder values
    best_Fmatrix = estimate_fundamental_matrix(matches1[0:9, :], matches2[0:9, :])
    best_inliers_a = matches1[0:29, :]
    best_inliers_b = matches2[0:29, :]
    best_inlier_residual = 5 # Arbitrary stencil code initial value placeholder.

    # For your report, we ask you to visualize RANSAC's 
    # convergence over iterations. 
    # For each iteration, append your inlier count and residual to the global variables:
    #   inlier_counts = []
    #   inlier_residuals = []
    # Then add flag --visualize-ransac to plot these using visualize_ransac()
    # print(matches1.shape, matches2.shape)
    max_inliers = 0
    inlier_threshold = 0.1
    for _ in range(num_iters):
        indices = np.random.randint(0, matches1.shape[0], size=(9,))
        sample1 = matches1[indices]
        sample2 = matches2[indices]
        # F_matrix, _ = cv2.findFundamentalMat(sample1, sample2, cv2.FM_8POINT, 1e10, 0, 1)
        F_matrix, residual = estimate_fundamental_matrix(sample1, sample2)
        # print(F_matrix.shape, F_matrix)
        matches1_homo = np.hstack((matches1, np.ones(shape=(matches1.shape[0], 1))))
        matches2_homo = np.hstack((matches2, np.ones(shape=(matches2.shape[0], 1))))

        res = np.array([m1 @ F_matrix @ m2 for m1, m2 in zip(matches1_homo, matches2_homo)])
        # res = matches1_homo @ F_matrix @ (matches2_homo.T)
        # print(res.shape, res)
        inliers_indices = np.abs(res) < inlier_threshold
        # print(inliers_indices)
        inliers1 = matches1[inliers_indices]
        inliers2 = matches2[inliers_indices]
        # print(inliers1.shape, inliers2.shape)

        if inliers1.shape[0] > max_inliers:
            best_Fmatrix = F_matrix
            best_inliers_a = inliers1
            best_inliers_b = inliers2
            max_inliers = inliers1.shape[0]
        
        inlier_counts.append(inliers1.shape[0])
        inlier_residuals.append(residual)

    return best_Fmatrix, best_inliers_a, best_inliers_b, best_inlier_residual

def matches_to_3d(points2d_1, points2d_2, M1, M2, threshold=1.0):
    """
    Given two sets of corresponding 2D points and two projection matrices, you will need to solve
    for the ground-truth 3D points using np.linalg.lstsq().

    You may find that some 3D points have high residual/error, in which case you 
    can return a subset of the 3D points that lie within a certain threshold.
    In this case, also return subsets of the initial points2d_1, points2d_2 that
    correspond to this new inlier set. You may modify the default value of threshold above.
    All local helper code that calls this function will use this default value, but we
    will pass in a different value when autograding.

    N is the input number of point correspondences
    M is the output number of 3D points / inlier point correspondences; M could equal N.

    :param points2d_1: [N x 2] points from image1
    :param points2d_2: [N x 2] points from image2
    :param M1: [3 x 4] projection matrix of image1
    :param M2: [3 x 4] projection matrix of image2
    :param threshold: scalar value representing the maximum allowed residual for a solved 3D point

    :return points3d_inlier: [M x 3] NumPy array of solved ground truth 3D points for each pair of 2D
    points from points2d_1 and points2d_2
    :return points2d_1_inlier: [M x 2] points as subset of inlier points from points2d_1
    :return points2d_2_inlier: [M x 2] points as subset of inlier points from points2d_2
    """
    ########################
    # TODO: Your code here #

    # Initial random values for 3D points
    # points3d_inlier = np.random.rand(len(points2d_1), 3)
    # points2d_1_inlier = np.array(points2d_1, copy=True) # only modify if using threshold
    # points2d_2_inlier = np.array(points2d_2, copy=True) # only modify if using threshold
    points3d_inlier = []
    points2d_1_inlier = []
    points2d_2_inlier = []

    # Solve for ground truth points
    for i in range(points2d_1.shape[0]):
        u1, v1 = points2d_1[i, 0], points2d_1[i, 1]
        u2, v2 = points2d_2[i, 0], points2d_2[i, 1]

        # construct A on the left side
        A = np.zeros((4, 3))
        A[0, :] = M1[2, 0:3] * u1 - M1[0, 0:3]
        A[1, :] = M1[2, 0:3] * v1 - M1[1, 0:3]
        A[2, :] = M2[2, 0:3] * u2 - M2[0, 0:3]
        A[3, :] = M2[2, 0:3] * v2 - M2[1, 0:3]

        # construct b on the right side
        b = np.zeros((4, 1))
        b[0] = M1[0, 3] - M1[2, 3] * u1
        b[1] = M1[1, 3] - M1[2, 3] * v1
        b[2] = M2[0, 3] - M2[2, 3] * u2
        b[3] = M2[1, 3] - M2[2, 3] * v2

        # print("A", A)
        # print("b", b)

        lstsq = np.linalg.lstsq(A, b)
        XYZ, residual = lstsq[0], lstsq[1]
        # print(XYZ.shape)
        # print(f"XYZ = {XYZ}")
        # print(f"residual = {residual}")
        if residual < threshold:
            points3d_inlier.append(XYZ.flatten())
            points2d_1_inlier.append(points2d_1[i])
            points2d_2_inlier.append(points2d_2[i])

    points3d_inlier = np.array(points3d_inlier)
    points2d_1_inlier = np.array(points2d_1_inlier)
    points2d_2_inlier = np.array(points2d_2_inlier)
    # print(points3d_inlier.shape)
    ########################

    return points3d_inlier, points2d_1_inlier, points2d_2_inlier


#/////////////////////////////DO NOT CHANGE BELOW LINE///////////////////////////////
inlier_counts = []
inlier_residuals = []

def visualize_ransac():
    iterations = np.arange(len(inlier_counts))
    best_inlier_counts = np.maximum.accumulate(inlier_counts)
    best_inlier_residuals = np.minimum.accumulate(inlier_residuals)

    plt.figure(1, figsize = (8, 8))
    plt.subplot(211)
    plt.plot(iterations, inlier_counts, label='Current Inlier Count', color='red')
    plt.plot(iterations, best_inlier_counts, label='Best Inlier Count', color='blue')
    plt.xlabel("Iteration")
    plt.ylabel("Number of Inliers")
    plt.title('Current Inliers vs. Best Inliers per Iteration')
    plt.legend()

    plt.subplot(212)
    plt.plot(iterations, inlier_residuals, label='Current Inlier Residual', color='red')
    plt.plot(iterations, best_inlier_residuals, label='Best Inlier Residual', color='blue')
    plt.xlabel("Iteration")
    plt.ylabel("Residual")
    plt.title('Current Residual vs. Best Residual per Iteration')
    plt.legend()
    plt.show()
