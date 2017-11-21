import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os


g_output_size = 784
g_input_size = 100
g_hidden_size = 128
minibatch_size = 128
num_epochs = 1000000
learning_rate = 1e-3

def load_data():
    from tensorflow.examples.tutorials.mnist import input_data
    mnist = input_data.read_data_sets("../MNIST_data/", one_hot=True)
    return mnist

def sample_Z_pytorch():
    return lambda minibatch_size, input_size: torch.nn.init.xavier_uniform(torch.Tensor(minibatch_size, input_size))  # uniform distribution

def plot(samples):
    fig = plt.figure(figsize=(5, 5))
    gs = gridspec.GridSpec(5, 5)
    gs.update(wspace=0.05, hspace=0.05)

    for i, sample in enumerate(samples):
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        plt.imshow(sample.reshape(28, 28), cmap='Greys_r')

    return fig

class gNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(gNet, self).__init__()
        self.Gen_h1 = nn.Linear(input_size, hidden_size)
        self.Gen_out = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.elu(self.Gen_h1(x))
        x = F.sigmoid(self.Gen_out(x))
        return x


class dNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(dNet, self).__init__()
        self.Dis_h1 = nn.Linear(input_size, hidden_size)
        self.Dis_h1_dropout = nn.Dropout(p=0.5)  # keep_prob = 0.5
        self.Dis_o = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.elu(self.Dis_h1(x))
        x = self.Dis_h1_dropout(x)
        x = F.sigmoid(self.Dis_o(x))
        return x

def trainGAN_pt():

    mnist = load_data()

    gnet = gNet(input_size = g_input_size, hidden_size = g_hidden_size, output_size = g_output_size)
    dnet = dNet(input_size = g_output_size, hidden_size = g_hidden_size, output_size = 1)
    z_sampler_pt = sample_Z_pytorch()
    loss = nn.BCELoss()
    ones_label = Variable(torch.ones(minibatch_size))
    zeros_label = Variable(torch.zeros(minibatch_size))
    Gen_optimizer_pt = optim.Adam(gnet.parameters(), lr= learning_rate)
    Dis_optimizer_pt = optim.Adam(dnet.parameters(), lr= learning_rate)

    if not os.path.exists('out_pt/'):
        os.makedirs('out_pt/')
    num_img = 0
    for epoch in range(num_epochs):
        # sample data
        Z_pt = Variable(z_sampler_pt(minibatch_size, g_input_size))
        X_minibatch_pt, _ = mnist.train.next_batch(minibatch_size)
        X_minibatch_pt = Variable(torch.from_numpy(X_minibatch_pt))  # convert from numpy to tensor

        Dis_optimizer_pt.zero_grad()

        Gen_sample_pt = gnet(Z_pt)
        Dis_real_pt = dnet(X_minibatch_pt)
        Dis_fake_pt = dnet(Gen_sample_pt)

        Dis_real_loss_pt = loss(Dis_real_pt, ones_label)
        Dis_fake_loss_pt = loss(Dis_fake_pt, zeros_label)
        Dis_loss_pt = Dis_real_loss_pt + Dis_fake_loss_pt

        Dis_loss_pt.backward(retain_graph=True)
        Dis_optimizer_pt.step()

        Gen_optimizer_pt.zero_grad()

        Gen_loss_pt = loss(Dis_fake_pt, ones_label)


        Gen_loss_pt.backward(retain_graph=True)
        Gen_optimizer_pt.step()


        # we save images generated by the generator every 1000 epochs
        if epoch % 1000 == 0:
            print(
            'Epoch-{}; dis_loss_pt: {}; gen_loss_pt: {}'.format(epoch, Dis_loss_pt.data.numpy(), Gen_loss_pt.data.numpy()))

            samples_pt = gnet(Z_pt).data.numpy()[:25]

            fig = plot(samples_pt)

            plt.savefig('out_pt/{}.png'.format(str(num_img).zfill(3)), bbox_inches='tight')
            num_img += 1
            plt.close(fig)

if __name__ == '__main__':
    trainGAN_pt()