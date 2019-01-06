import numpy as np
from CustomDistances import sq_distance, hv_distance
import CustomKernels
from sklearn.metrics import mean_squared_error
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel, RBF, RationalQuadratic, ConstantKernel as C
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.svm import SVR
from pyearth import Earth
    
class LearningModel:
    
    def __init__(self):
        pass
        
    def train(self, X, Y, eval_score=False):
        pass
        
    def predict(self, X_out, Y_out=None, eval_score=False):
        pass
    
    def _score(self, Y, prediction):
        return mean_squared_error(Y, prediction)
    

class NearestNeighbor(LearningModel):
    
    def __init__(self):
        pass
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):
        nsample = self.X_in.shape[0]
        npreds = X_out.shape[0]
        prediction = np.empty([npreds,1])
    
        ##Vectorized operation is slower than for-loop
        #distance = hv_distance(X_out[:,0,None], X_out[:,1,None], self.X_in[:,0], self.X_in[:,1])
        #print(distance)
        #prediction = self.Y_in[np.argmin(distance, axis=1)]
    
        for k in range(0, npreds):
            distance = hv_distance(X_out[k][0], X_out[k][1], self.X_in[:,0], self.X_in[:,1])
            prediction[k] = self.Y_in[np.argmin(distance)]
        
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction
        
    
class InverseDistanceWeighting(LearningModel):
    
    radius = 500
    
    def __init__(self):
        pass
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):
        
        nsample = self.X_in.shape[0]
        npreds = X_out.shape[0]
        prediction = np.empty([npreds,1])
        
        for k in range(0, npreds):
            distance = hv_distance(X_out[k][0], X_out[k][1], self.X_in[:,0], self.X_in[:,1])
            idx0 = np.where(distance < 1)
            idx_in_radius = np.where(distance < self.radius)
            if idx_in_radius[0].size == 0 or idx0[0].size > 0:
                prediction[k] = self.Y_in[np.argmin(distance)]
            else:
                numerator = np.sum(self.Y_in[idx_in_radius][:,None]/distance[idx_in_radius][:,None])
                denominator = np.sum(1/distance[idx_in_radius][:,None])
                prediction[k] = numerator/denominator
        
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction
        
        
class GaussianProcess(LearningModel):
    
    kernel = C(1.0)*RBF(length_scale=[10.0, 10.0]) + WhiteKernel(0.1)
    
    def __init__(self):
        self.gpr = GaussianProcessRegressor(kernel=self.kernel, alpha = 0, optimizer=None, n_restarts_optimizer=10, 
                                       normalize_y=True, random_state=0)
        #gpr = GaussianProcessRegressor(kernel=kernel, alpha = 0, optimizer='fmin_l_bfgs_b', n_restarts_optimizer=10, 
        #                               normalize_y=True, random_state=0).fit(X, Y)
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.gpr.fit(self.X_in, self.Y_in)
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.gpr.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction


class GeographicallyWeightedRegressor(LearningModel):
    
    kernel = C(1.0)*CustomKernels.RBF(length_scale=100.0, metric='haversine') + WhiteKernel(0.1)
    
    def __init__(self):
        #self.gwr = GaussianProcessRegressor(kernel=self.kernel, alpha = 0, optimizer='fmin_l_bfgs_b', n_restarts_optimizer=10, 
        #                               normalize_y=True, random_state=0).fit(X, Y)
        self.gwr = GaussianProcessRegressor(kernel=self.kernel, alpha = 0, optimizer=None, n_restarts_optimizer=10, 
                                       normalize_y=True, random_state=0)
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.gwr.fit(self.X_in, self.Y_in)
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.gwr.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction

    

class RegressionTree(LearningModel):
    
    max_depth = 9
    
    def __init__(self):
        self.rtree = DecisionTreeRegressor(max_depth=self.max_depth)
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.rtree.fit(self.X_in, self.Y_in)
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.rtree.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction


class RandomForest(LearningModel):
    
    max_ntree = 1000
    max_depth = 10
    random_state = 42
    
    def __init__(self):
        self.rforest = RandomForestRegressor(n_estimators=self.max_ntree, max_features='auto', 
                                    max_depth=self.max_depth, random_state=self.random_state) 
        
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.rforest.fit(self.X_in, np.ravel(self.Y_in))
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.rforest.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction


class ExtraTrees(LearningModel):
    
    max_ntree = 1000
    max_depth = 10
    random_state = 42
    
    def __init__(self):
        self.extrees = ExtraTreesRegressor(n_estimators=self.max_ntree, max_features='auto', 
                                    max_depth=self.max_depth, random_state=self.random_state)
    
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.extrees.fit(self.X_in, np.ravel(self.Y_in))
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.extrees.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction
        

class SupportVectorRegression(LearningModel):
    
    C = 10.0
    epsilon = 5.0
    
    def __init__(self):
        self.svr = SVR(gamma='auto', C=self.C, epsilon=self.epsilon)
            
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.svr.fit(self.X_in, np.ravel(self.Y_in))
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.svr.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction

        
class RegressionSplines(LearningModel):
    
    max_degree = 3
    penalty = 3.0
    
    def __init__(self):
        self.splin = Earth(max_degree = self.max_degree, penalty = self.penalty)
            
    def train(self, X, Y, eval_score=False):
        assert X.shape[0] == Y.shape[0]
        self.X_in = X
        self.Y_in = Y
        self.splin.fit(self.X_in, self.Y_in)
        if eval_score:
            prediction, score = self.predict(self.X_in, self.Y_in, eval_score=True)
            return score
        
    def predict(self, X_out, Y_out=None, eval_score=False):   
        
        prediction = self.splin.predict(X_out)
        if eval_score:
            if Y_out is None:
                raise ValueError("Need Y_out (Y_test) to evaluate score")
            else:
                score = self._score(Y_out, prediction)
                return prediction, score
        else:
            return prediction
    