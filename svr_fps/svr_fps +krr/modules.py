from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd


def sub_data(File):
    data1=open(File,'r+')
    X=[]
    y=[]
    for i, line in enumerate(data1):
        data=line.split()
        #for j in range(int(len(data))-2):
        #    X += [float(data[j+1])]
        for j in range(int(len(data))-1):
            X += [float(data[j])]
        y += [float(data[-1])]
    m=len(X)
    n=len(y)
    X=np.array(X).reshape(int(n),int(m/n))
    y=np.array(y)
    return X,y


def pre_data(X,y):
    #y=preprocessing.scale(y)
    scaler=StandardScaler()
    scaler.fit(X)
    X=scaler.transform(X)
    return X,y
    #X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=50
    



def plot_learning_curve(estimator, title, X, y, ylim=None, cv=None, n_jobs=1,
                        train_sizes=np.linspace(.05, 1., 20), verbose=0, plot=True):
    """
    画出data在某模型上的learning curve.
    参数解释
    ----------
    estimator : 你用的分类器。
    title : 表格的标题。
    X : 输入的feature，numpy类型
    y : 输入的target vector
    ylim : tuple格式的(ymin, ymax), 设定图像中纵坐标的最低点和最高点
    cv : 做cross-validation的时候，数据分成的份数，其中一份作为cv集，其余n-1份作为training(默认为3份)
    n_jobs : 并行的的任务数(默认1)
    """
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes, verbose=verbose)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    print( train_sizes)
    if plot:

        plt.figure()
        plt.title(title)
        if ylim is not None:
            plt.ylim(*ylim)
        plt.xlabel("train size")
        plt.ylabel("score")
        #plt.ylim(0,1)
        #plt.gca().invert_yaxis()
        plt.grid()

        plt.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std,
                         alpha=0.1, color="b")
        plt.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std,
                         alpha=0.1, color="r")
        plt.plot(train_sizes, train_scores_mean, 'o-', color="b", label=u"train score")
        plt.plot(train_sizes, test_scores_mean, 'o-', color="r", label=u"test score")

        plt.legend(loc="best")

        plt.draw()
        plt.show()
        plt.gca().invert_yaxis()

    midpoint = ((train_scores_mean[-1] + train_scores_std[-1]) + (test_scores_mean[-1] - test_scores_std[-1])) / 2
    diff = (train_scores_mean[-1] + train_scores_std[-1]) - (test_scores_mean[-1] - test_scores_std[-1])
    return midpoint, diff

#plot_learning_curve(alg1,u"learn curve", train_data_X, train_data_Y)#画出
def plot_train_test_results(y_train,y_test,y_pre1,y_pre2,output=True,fname='GBR',plt_prop=True):
   train_typ,test_typ=[],[]
   for i in range(len(y_train)):
     train_typ+=['Train']
   for i in range(len(y_test)):
     test_typ+=['Test']
   data0=np.transpose(np.vstack((y_train,y_pre1)))
   d0=pd.DataFrame(data0,columns=['Calculated Values(Ωm2)','Predicted Values(Ωm2)'])

   data1=np.transpose(np.vstack((train_typ,y_train,y_pre1)))
   d1=pd.DataFrame(data1,columns=['Type','Calculated Values(Ωm2)','Predicted Values(Ωm2)'])

   data2=np.transpose(np.vstack((test_typ,y_test,y_pre2)))
   d2=pd.DataFrame(data2,columns=['Type','Calculated Values(Ωm2)','Predicted Values(Ωm2)'])

   data=np.vstack((data1,data2))
   d3=pd.DataFrame(data,columns=['Type','Calculated Values(Ωm2)','Predicted Values(Ωm2)'])
   d3["Calculated Values(Ωm2)"]=pd.to_numeric(d3["Calculated Values(Ωm2)"])
   d3["Predicted Values(Ωm2)"]=pd.to_numeric(d3["Predicted Values(Ωm2)"])

   #print(d3)
   #sns.jointplot(x=y_test, y=y_pre2,color='b',edgecolor='w',linewidth=1,space=0.0,height=10,ratio=10,xlim=(-7.5,1), ylim=(-7.5,1))
   #sns.jointplot(x='Calculated Values(eV)', y='Predicted Values(eV)',data=d0,color='b',edgecolor='w',linewidth=1,space=0.0,height=10,ratio=10,xlim=(-7.5,1), ylim=(-7.5,1))
   #sns.jointplot(data=d3,x="Calculated Values(eV)", y="Predicted Values(eV)",hue="Type",space=0.0,height=10,ratio=10,xlim=(-7.5,1), ylim=(-7.5,1),marginal_ticks=False)
   sns.set_context("talk",font_scale=1.5,rc={'font.size': 20.0,
 'legend.fontsize':20,
 'legend.title_fontsize':20, 
 'legend.loc':0 ,
 'axes.linewidth':2.0,
 'axes.labelsize': 20.0,
 'axes.titlesize': 20.0,
 'xtick.labelsize': 16.5,
 'ytick.labelsize': 16.5,})

   lim0=min(min(y_train),min(y_pre1),min(y_test),min(y_pre2))
   lim1=max(max(y_train),max(y_pre1),max(y_test),max(y_pre2))
 
   g=sns.JointGrid(x='Calculated Values(Ωm2)', y='Predicted Values(Ωm2)', hue='Type',data=d3,space=0.0,height=10,ratio=10,xlim=(lim0-0.1,lim1+0.1), ylim=(lim0-0.1,lim1+0.1))
   g.plot_joint(sns.scatterplot,s=150, palette="Set2")

   g.ax_joint.plot([lim0 - 0.3, lim1 + 0.3], [lim0 - 0.3, lim1 + 0.3], color='red', linestyle='--',linewidth=0.5,label='y=x')
   g.ax_joint.legend()
   g.plot_marginals(sns.kdeplot,shade=True,palette="Set2",common_norm=False)
  
   '''
   g=sns.JointGrid(x='Calculated Values(eV)', y='Predicted Values(eV)', data=d3)
   g=g.plot_joint(plt.scatter,color='g',s=40,edgecolor='white')
   plt.grid(linestyle='--')
   #g.plot_marginals(sns.distplot,kde=True,color='g')
   g.plot_marginals(sns.kdeplot,shade=True,color='g')
   '''
   
   if output:
      plt.savefig(f'{fname}.png',dpi=300)
   if plt_prop:
      plt.show()
        
