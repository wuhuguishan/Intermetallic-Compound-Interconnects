import math
import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn import manifold
from scipy.stats import pearsonr
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor as GPR
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel,RBF,ConstantKernel as const

from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt 
import seaborn as sns


def data_dist(X,y,cluster=1,bound=0,output=True,title='prediction',fname='data_dis',loc='.',plt_prop=True):

  '''t-SNE'''
  tsne = manifold.TSNE(n_components=2,init='pca', random_state=501)
  X_tsne = tsne.fit_transform(X)
  print("Org data dimension is {}.Embedded data dimension is {}".format(X.shape[-1], X_tsne.shape[-1]))

  '''visualization'''
  x_min, x_max = X_tsne.min(0), X_tsne.max(0)
  X_norm = (X_tsne - x_min) / (x_max - x_min)  # 归一化
  plt.figure(figsize=(12,6))
  plt.xticks(fontsize=15)
  plt.yticks(fontsize=15)
  plt.title(title,fontsize=20)
  ax=plt.gca()
  ax.spines['bottom'].set_linewidth(2)
  ax.spines['left'].set_linewidth(2)
  ax.spines['top'].set_linewidth(2)
  ax.spines['right'].set_linewidth(2)
  if cluster == 1:
    if y:
      path=plt.scatter(X_norm[:, 0], X_norm[:, 1],c=y, cmap=plt.cm.rainbow)
      cb=plt.colorbar(drawedges=False, orientation='vertical',spacing='uniform')
      cb.set_label('Binding Energy/eV', fontsize=15)
      cb.ax.tick_params(size=5,width=1,labelsize=12)
    else:
      path=plt.scatter(X_norm[:, 0], X_norm[:, 1], cmap=plt.cm.rainbow)
  if cluster == 2:
    if y:
      plt.scatter(X_norm[0:bound, 0], X_norm[0:bound, 1],c=y, cmap=plt.cm.rainbow)
      plt.scatter(X_norm[bound:, 0], X_norm[bound:, 1],c=y, cmap=plt.cm.rainbow)
      cb=plt.colorbar(drawedges=False, orientation='vertical',spacing='uniform')
      cb.set_label('Binding Energy/eV', fontsize=15)
      cb.ax.tick_params(size=5,width=1,labelsize=12)
    else:
      plt.scatter(X_norm[0:bound, 0], X_norm[0:bound, 1], c='r',s=35,marker='p',alpha=0.75)
      plt.scatter(X_norm[bound:, 0], X_norm[bound:, 1], c='b',s=35,marker='*',alpha=0.5)


  if output:
    plt.savefig(f'{loc}/{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
    plt.show()

def data_dist_density(X,y,cluster=1,bound=0,output=True,title='prediction',fname='data_dis',loc='.',plt_prop=True,patt='Set2'):

  '''t-SNE'''
  tsne = manifold.TSNE(n_components=2,init='pca', random_state=501)
  X_tsne = tsne.fit_transform(X)
  print("Org data dimension is {}.Embedded data dimension is {}".format(X.shape[-1], X_tsne.shape[-1]))

  '''visualization'''
  x_min, x_max = X_tsne.min(0), X_tsne.max(0)
  X_norm = (X_tsne - x_min) / (x_max - x_min)  # 归一化i
  '''
  plt.figure(figsize=(12,10))
  plt.xticks(fontsize=15)
  plt.yticks(fontsize=15)
  plt.title(title,fontsize=20)
  ax=plt.gca()
  ax.spines['bottom'].set_linewidth(2)
  ax.spines['left'].set_linewidth(2)
  ax.spines['top'].set_linewidth(2)
  ax.spines['right'].set_linewidth(2)
  '''
  print(list(X_norm[100]))
  typ=[]  
  for i in range(X_norm.shape[0]):
      if i < bound:
         typ += ['Initial set']
      else:
         typ += ['Search set']
 
  data0=np.transpose(np.vstack((np.transpose(X_norm),typ)))
  d=pd.DataFrame(data0,columns=['PC1','PC2','Type'])
  d["PC1"]=pd.to_numeric(d["PC1"])
  d["PC2"]=pd.to_numeric(d["PC2"])

  sns.set_context("talk",font_scale=1.5,rc={'font.size': 20.0,
 'legend.fontsize':20,
 'legend.title_fontsize':20,
 'axes.linewidth':2.0,
 'axes.labelsize': 20.0,
 'axes.titlesize': 20.0,
 'xtick.labelsize': 16.5,
 'ytick.labelsize': 16.5,})
  
  if cluster == 2:
    if y:
      print('No Support')
      
    else:
      g=sns.JointGrid(x='PC1', y='PC2', hue='Type',data=d,space=0.0,height=10,ratio=10,xlim=(-0.1,1.1), ylim=(-0.1,1.1))
      #g=sns.JointGrid(x='PC1', y='PC2',data=d,space=0.0,height=10,ratio=10,xlim=(-0.1,1.1), ylim=(-0.1,1.1))
      g.plot_joint(sns.scatterplot,s=50, palette=patt,legend='auto')
      #aa.legend(loc='upper center',frameon=False,title='type',)
      #sns.move_legend(g, "center left")
      g.plot_marginals(sns.kdeplot,shade=True,common_norm=False,palette=patt)
      #plt.legend(loc='upper center',frameon=False,title='Clusters')  
      g.set_axis_labels()
     
  if output:
    plt.savefig(f'{loc}/{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
    plt.show()

def data_scatter(y1,y2,label1='E(N)',label2='E(O)',output=True,title='prediction',fname='data_dis',loc='.',plt_prop=True,patt='Set2',c='r'):
  plt.figure(figsize=(12,10))
  plt.xticks(fontsize=22)
  plt.yticks(fontsize=22)
  plt.tick_params(axis='x',width=2,length=10)
  plt.tick_params(axis='y',width=2,length=10)
  plt.xlabel(label1,fontsize=25)
  plt.ylabel(label2,fontsize=25)
  plt.title(title,fontsize=25)
  plt.grid(ls='-.')
  ax=plt.gca()
  ax.spines['bottom'].set_linewidth(3)
  ax.spines['left'].set_linewidth(3)
  ax.spines['top'].set_linewidth(3)
  ax.spines['right'].set_linewidth(3)
  
  plt.scatter(y1,y2,color=c,s=75,alpha=0.5)#cmap=plt.cm.rainbow)

  if output:
    plt.savefig(f'{loc}/{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
    plt.show()
def data_scatter_2(y1,y2,label1='E(N)',label2='E(O)',output=True,title='prediction',fname='data_dis',loc='.',plt_prop=True,patt='Set2',c='r'):
  sns.set_context("talk",font_scale=1.5,rc={'font.size': 20.0,
 'legend.fontsize':20,
 'legend.title_fontsize':20,
 'axes.linewidth':2.0,
 'axes.labelsize': 20.0,
 'axes.titlesize': 20.0,
 'xtick.labelsize': 16.5,
 'ytick.labelsize': 16.5,})

  #sns.jointplot(x=y1, y=y2, kind="hex", color=c, size = 7)
  sns.jointplot(x=y1, y=y2, kind="hex", color=c)
  #cb=plt.colorbar(drawedges=False, orientation='vertical',spacing='uniform')
  #cb.set_label('Binding Energy/eV', fontsize=15)
  #cb.ax.tick_params(size=5,width=1,labelsize=12)

  if output:
    plt.savefig(f'{loc}/{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
    plt.show()


#plot_learning_curve(alg1,u"learn curve", train_data_X, train_data_Y)#画出
def plot_train_test_results(y_train,y_test,y_pre1,y_pre2,output=True,fname='GBR',plt_prop=True,patt='Set2'):
   train_typ,test_typ=[],[]
   for i in range(len(y_train)):
     train_typ+=['Train']
   for i in range(len(y_test)):
     test_typ+=['Test']
   data0=np.transpose(np.vstack((y_train,y_pre1)))
   d0=pd.DataFrame(data0,columns=['Calculated Values(eV)','Predicted Values(eV)'])

   data1=np.transpose(np.vstack((train_typ,y_train,y_pre1)))
   d1=pd.DataFrame(data1,columns=['Type','Calculated Values(eV)','Predicted Values(eV)'])

   data2=np.transpose(np.vstack((test_typ,y_test,y_pre2)))
   d2=pd.DataFrame(data2,columns=['Type','Calculated Values(eV)','Predicted Values(eV)'])

   data=np.vstack((data1,data2))
   d3=pd.DataFrame(data,columns=['Type','Calculated Values(eV)','Predicted Values(eV)'])
   d3["Calculated Values(eV)"]=pd.to_numeric(d3["Calculated Values(eV)"])
   d3["Predicted Values(eV)"]=pd.to_numeric(d3["Predicted Values(eV)"])
   t1=max(max(d3["Calculated Values(eV)"]),max(d3["Predicted Values(eV)"]))
   t2=min(min(d3["Calculated Values(eV)"]),min(d3["Predicted Values(eV)"]))
   #print(t1,t2)
   #print(math.ceil(t1),math.ceil(t2))
   #print(t1//1,t2//1)
   max_lim=max(math.ceil(t1),t1//1)+0.5
   min_lim=min(math.ceil(t2),t2//1)-0.5
 
   sns.set_context("talk",font_scale=1.5,rc={'font.size': 25.0,
 'legend.fontsize':20,
 'legend.title_fontsize':20,
 'axes.linewidth':2.0,
 'axes.labelsize': 20.0,
 'axes.titlesize': 20.0,
 'xtick.labelsize': 16.5,
 'ytick.labelsize': 16.5,})

   g=sns.JointGrid(x='Calculated Values(eV)', y='Predicted Values(eV)', hue='Type',data=d3,space=0.0,height=10,ratio=10,xlim=(min_lim,max_lim), ylim=(min_lim,max_lim))
   #g=sns.JointGrid(x='Calculated Values(eV)', y='Predicted Values(eV)', hue='Type',data=d3,space=0.0,height=10,ratio=10,xlim=(-7.5,1), ylim=(-7.5,1))
   g.plot_joint(sns.scatterplot,s=75, palette=patt,legend='auto')
   g.plot_marginals(sns.kdeplot,fill=True,palette=patt,common_norm=False)

   if output:
      plt.savefig(f'{fname}.png',dpi=300)
   if plt_prop:
      plt.show()
def plot_bar(feat,label,output=True,fname='feat_import',plt_prop=True):
   plt.figure(figsize=(12,10))
   plt.grid(axis='x',ls='--')
   feat1=list(reversed(feat))
   label1=list(reversed(label))
   #plt.yticks(rotation=30)

   plt.xticks(fontsize=18)
   plt.yticks(fontsize=18)
   plt.axis([0,1.0,-1,5])
   ax=plt.gca()
   ax.spines['bottom'].set_linewidth(2)
   ax.spines['left'].set_linewidth(2)
   ax.spines['top'].set_linewidth(2)
   ax.spines['right'].set_linewidth(2)
   #plt.grid()
   plt.xlabel(u'Explained_variance_ratio',fontsize=20)
   plt.ylabel(u'Components',fontsize=20)
   plt.barh(range(len(feat1)),feat1,tick_label=label1,fc='red',alpha=0.75)
   #feat1= [round(i,3) for i in feat1]
   for xx,yy in zip(range(len(feat1)),feat1):
      print(xx,yy)
      plt.text(yy+0.05,xx,round(yy,3),ha='center',va='center',fontsize=18)
   if output:
      plt.savefig(f'{fname}.png',dpi=300,bbox_inches='tight')
   if plt_prop:
      plt.show()
def plot_bar2(feat1,feat2,label,plt_prop=True,output=True,fname='GPRmodel',color='Dark2'):
   bar_width = 0.15 
 
   x0=np.arange(len(feat1))
   x1=x0-bar_width
   x2=x0+bar_width
   
   #fig, ax1=plt.subplots()
   c='.'.join(['plt.cm',color])
   c=eval(c)
   c1=c(0)
   c2=c(1)
   #c1=plt.cm.Set2(0)
   #c2=plt.cm.Set2(1)
   fig=plt.figure(figsize=(12,6))
   ax1=fig.add_subplot(111)
   ax=plt.gca()
   ax.spines['bottom'].set_linewidth(2)
   ax.spines['left'].set_linewidth(2)
   ax.spines['top'].set_linewidth(2)
   ax.spines['right'].set_linewidth(2)
   
   #ax1.set_xlabel(' ')
   ax1.set_ylabel('Score',color=c1,fontsize=22)   
   ax1.bar(x1[0],feat1[0],tick_label=label[0],color=c1,alpha=1,width=0.3)
   ax1.bar(x2[0],feat2[0],color=c1,alpha=0.75,width=0.3)
   ax1.tick_params(axis='x',width=2,labelsize=22,labelbottom=True)
   #plt.xticks(['R2','MAE','RMSE'])
   ax1.tick_params(axis='y',labelsize=22,labelcolor=c1,width=2)
   # add the values
   d=0.02
   for xx,yy in zip([x1[0]],[feat1[0]]):
      yy1=f'{yy:.3f}'
      plt.text(xx,yy+d,yy1,ha='center',va='center',fontsize=20)
   for xx,yy in zip([x2[0]],[feat2[0]]):
      yy1=f'{yy:.3f}'
      plt.text(xx,yy+d,yy1,ha='center',va='center',fontsize=20)
   
   plt.xlim([-0.5,2.5])
   plt.ylim([0.0,1.1]) 
   fig.legend(['Train','Test'],loc=(0.35,0.688),fontsize=25,frameon=False)
  
   #plt.grid(axis='y',ls='--')

   ax2=ax1.twinx()
   ax2.set_ylabel('Error/eV',color=c2,fontsize=22)
   ax2.bar(x1[1:],feat1[1:],color=c2,alpha=1,width=0.3)
   ax2.bar(x2[1:],feat2[1:],color=c2,alpha=0.75,width=0.3)
   ax2.tick_params(axis='y',labelsize=20,labelcolor=c2,width=2)
   

   #plt.yticks(fontsize=18) 
   # add the values
   d=0.0075
   #loc='upper right'
   loc=(0.60,0.75)
   for xx,yy in zip(x1[1:],feat1[1:]):
      yy1=f'{yy:.3f}'
      plt.text(xx,yy+d,yy1,ha='center',va='center',fontsize=20)
   for xx,yy in zip(x2[1:],feat2[1:]):
      yy1=f'{yy:.3f}'
      plt.text(xx,yy+d,yy1,ha='center',va='center',fontsize=20)
   ymax=max(max(feat1[1:]),max(feat2[1:]))+0.1
   plt.ylim([0.0,ymax])
   plt.legend(['Train','Test'],loc=loc,fontsize=25,frameon=False) 

   ax3=ax1.twinx()
   ax3.bar(x0,[0,0,0],tick_label=label)
   ax3.tick_params(axis='y',labelright=False,right=False) 
   
   if output:
      plt.savefig(f'{fname}.png',dpi=300,bbox_inches='tight')
   if plt_prop:
      plt.show()

def corre_linear(X,label,y=None,mask_typ=True,output=True,fname='feat_corr', plt_prop=True):
  score_matrix0=[]
  score_matrix=[]
  m,n=X.shape
  for i in range(n):
    for j in range(n):
      score_matrix0 += [pearsonr(X[:,i],X[:,j])[0]]
  for i in score_matrix0:
    if abs(i) < 0.01:
       score_matrix += [0.00]
    else:
       score_matrix += [round(i,2)]
  score_matrix = np.array(score_matrix).reshape(n,n)

  mask = np.zeros_like(score_matrix, dtype=np.bool_)
  mask[np.triu_indices_from(mask,k=1)] = True
 
  #d1=pd.DataFrame(score_matrix,index=['ave_elec_surf','ave_rad_surf','ave_elec_sub','ave_rad_sub','Ncoord','typ_site'],columns=['ave_elec_surf','ave_rad_surf','ave_elec_sub','ave_rad_sub','Ncoord','typ_site'])
  d1=pd.DataFrame(score_matrix,index=label,columns=label)
  cmap = sns.cubehelix_palette(start = 1.5, rot = 3, gamma=0.8, as_cmap = True)
  if mask_typ :
     sh=sns.heatmap(d1,vmin=-1,vmax=1,square=True, linewidths=1.5,center=True,mask=mask,annot=True,cmap=cmap,cbar=False,annot_kws={"size":10})
  else:
     sh=sns.heatmap(d1,vmin=-1,vmax=1,square=True, linewidths=1.5,center=True,annot=True,cmap=cmap,cbar=False,annot_kws={"size":10})
     
     
  sh.set_xticklabels(sh.get_xticklabels(),rotation=60)
  ### colorbar sets ###
  cb=sh.figure.colorbar(sh.collections[0])
  cb.ax.tick_params(labelsize=10)
  cb.set_label('Correlation Coffecient',fontsize=10)
  
  if output:
     plt.savefig(f'{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
     plt.savefig('linear.png',dpi=300,bbox_inches='tight')
     plt.show()
     
  return score_matrix
def corre_spearman(X,label,y=None,mask_typ=True,output=True,fname='feat_corr', plt_prop=True):
  score_matrix0=[]
  score_matrix=[]

  x = pd.DataFrame(X)
  score_matrix0=x.corr("spearman")
  score_matrix0[score_matrix0<0.01]=0
  score_matrix = score_matrix0.values

  mask = np.zeros_like(score_matrix, dtype=np.bool_)
  mask[np.triu_indices_from(mask,k=1)] = True
 
  #d1=pd.DataFrame(score_matrix,index=['ave_elec_surf','ave_rad_surf','ave_elec_sub','ave_rad_sub','Ncoord','typ_site'],columns=['ave_elec_surf','ave_rad_surf','ave_elec_sub','ave_rad_sub','Ncoord','typ_site'])
  d1=pd.DataFrame(score_matrix,index=label,columns=label)
  cmap = sns.cubehelix_palette(start = 1.5, rot = 3, gamma=0.8, as_cmap = True)
  if mask_typ :
     sh=sns.heatmap(d1,vmin=-1,vmax=1,square=True, linewidths=1.5,center=True,mask=mask,annot=True,cmap=cmap,cbar=False,annot_kws={"size":10})
  else:
     sh=sns.heatmap(d1,vmin=-1,vmax=1,square=True, linewidths=1.5,center=True,annot=True,cmap=cmap,cbar=False,annot_kws={"size":10})
     
     
  sh.set_xticklabels(sh.get_xticklabels(),rotation=60)
  ### colorbar sets ###
  cb=sh.figure.colorbar(sh.collections[0])
  cb.ax.tick_params(labelsize=10)
  cb.set_label('Correlation Coffecient',fontsize=10)
  
  if output:
     plt.savefig(f'{fname}.png',dpi=300,bbox_inches='tight')
  if plt_prop:
     plt.savefig('spearman.png',dpi=300,bbox_inches='tight')
     plt.show()
     
  return score_matrix
    
def feat_import(X,y,label,output=True,fname='feat_import', plt_prop=True):
   regr=GradientBoostingRegressor(n_estimators=100,max_depth=5,learning_rate=0.1,random_state=0)
   regr.fit(X, y)
   feat=regr.feature_importances_

   #plot_bar(feat,label,output=True,fname=f'feat_import',plt_prop=True)
   plt.figure(figsize=(12,10))
   feat1=list(reversed(feat))
   label1=list(reversed(label))
   plt.grid(axis='x',ls='--')
   ax=plt.gca()
   ax.spines['bottom'].set_linewidth(2)
   ax.spines['left'].set_linewidth(2)
   ax.spines['top'].set_linewidth(2)
   ax.spines['right'].set_linewidth(2)

   xm=max(feat)+0.1
   ym=len(label)
   plt.axis([0,xm,-1,ym])

   plt.xticks(fontsize=18)
   plt.yticks(fontsize=18)
   
   plt.xlabel(u'Feature Importance',fontsize=20)
   plt.ylabel(u'Features',fontsize=20)
   
   plt.barh(range(len(feat1)),feat1,tick_label=label1,fc='red',alpha=0.75)
   for xx,yy in zip(range(len(feat1)),feat1):
      #print(xx,yy)
      plt.text(yy+0.02,xx,round(yy,3),ha='center',va='center',fontsize=18)
   if output:
      plt.savefig(f'{fname}.png',dpi=300,bbox_inches='tight')
   if plt_prop:
      plt.show()
   return feat
if __name__ == '__main__':
   File01 = '../data/data-N'
   File02 = '../data/data-O'
   label=['Ebase','Edop','Num','ave_elec_surf','ave_rad_surf','ave_elec_sub','ave_rad_sub','Ncoord']
   File11='../data/data-N-pred'
   File12='../data/data-O-pred'
   
   print('00-data Extraction')
   #X1,y1,X2,y2,base,label_sys,set_none,set_extre=sub_data_double(File01,File02)
   X1,y1,X2,y2,base,label_sys,set_none,set_extre=sub_data_double(File11,File12,y_pro=False)
   #print(base,label_sys)

   #X11,label11,base11=sub_data_noY(File11)
   #X12,label12,base12=sub_data_noY(File12)
   
   '''
   print('01-data distributin')
   data_dist(X1,y1,output=False,title='E(N) prediction',fname='data_dist',plt_prop=True)
   data_dist(X2,y2,output=False,title='E(O) prediction',fname='data_dist',plt_prop=True)
   '''
   #bound=X1.shape[0]
   #X=np.vstack((X1,X11))
   #data_dist(X,y=None,cluster=2,bound=bound,output=False,title='E(N) prediction',fname='data_dist',plt_prop=True)
   '''
   print('02-data preprocess')
   X1,y1=pre_data_N(X1,y1)
   X2,y2=pre_data_O(X2,y2)
   init_set,init_set_label=init_pareto_set_2D(y1,y2,label_sys)
   #print(init_set,init_set_label)
   '''
   #y11_pre,y11_std=gpr_Ead_pred(X1,y1,X11)
   #y12_pre,y12_std=gpr_Ead_pred(X2,y2,X12)
   
   #y1=np.hstack((y1,y11_pre))
   #y2=np.hstack((y2,y12_pre))
   #init_set,init_set_label=init_pareto_set_2D(y1,y2,label_sys)
    
   ''' 
   set_r,set_label_r=rank_goal(init_set,init_set_label) 
   #print(set_r[0][0],set_label_r)
   yall=np.vstack((y1,y2)).T
   plot_pareto_set_front_2D(set_r,yall)
   '''
   '''  
   print('03-feature correlation of data based on pearson coffecient')
   corre_linear(X1,y1,label)
   corre_linear(X2,y2,label)
   print('04-feature importance of data based on tree-based model')
   feat_import(X1,y1,label,output=False,title='E(N) prediction',fname='feat_import',plt_prop=True)
   feat_import(X1,y1,label,output=False,title='E(O) prediction',fname='feat_import',plt_prop=True)
   print('05-prediction of goals')
   y_pre1,y1_std=gpr_Ead_test(X1,y1,label1)
   y_pre2,y2_std=gpr_Ead_test(X2,y2,label2)
   '''
