#    Copyright 2014 Romain Mari
#    This file is part of Homer.
#
#    Homer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from string import *
import sys, os
import numpy as np
import io
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *
import homerFrame

color_fname = "homer_palette.py"
if os.path.isfile(color_fname):
    sys.path.append(".")
    import homer_palette
    color_palette = np.array(homer_palette.color_palette)
else:
    color_palette = np.array([Qt.black, Qt.gray, Qt.white, Qt.green, Qt.yellow, Qt.red, Qt.blue, Qt.magenta, Qt.darkGreen, Qt.cyan, Qt.gray, Qt.white, Qt.green, Qt.yellow, Qt.red, Qt.blue, Qt.magenta, Qt.darkGreen, Qt.cyan])

class homerFile:
    def __init__(self, filename):
        
        self.is_file=True
        self.fname=filename
        self.chunksize = 5000000#10000000
        self.frames = []
        self.read_all = False
        self.infile = open(self.fname,'r')
        self.trailing_frame = []
        self.trailing_attributes = []

    def getBoundaries(self):
        return self.frames[0].getBoundaries()
    
    def read_chunk(self):
        if self.read_all:
            return False

        ftype = np.float32

        in_raw_data = np.core.defchararray.partition(np.asarray(self.infile.readlines(self.chunksize), dtype=np.str_), ' ')
        if in_raw_data.shape[0] == 0:
            self.read_all = True
            return False
        
        in_raw_data = in_raw_data[:,[0,2]]
                
        while not np.any(in_raw_data[:,0]=='\n'):
            b =  np.core.defchararray.partition(np.asarray(self.infile.readlines(self.chunksize), dtype=np.str_), ' ')
            if b.shape[0] == 0:
                break
            b = b[:,[0,2]]
            in_raw_data=np.vstack((in_raw_data,b))

        obj_nb = np.shape(in_raw_data)[0]

        attributes = np.zeros(obj_nb, dtype=[('r', ftype), ('@', np.object), ('y', ftype)])
        all_att_mask = np.ones(obj_nb, dtype=np.bool)
        for at in ['r','y']:
            att_mask = in_raw_data[:,0]==at
            all_att_mask -= att_mask
            pos = np.nonzero(att_mask)[0] # locate the attributes changes
            if len(self.trailing_attributes):
                attributes[at][:pos[0]] = self.trailing_attributes[at][-1]
                
            if len(pos)>0:
                for i in range(len(pos)-1):
                    attributes[at][pos[i]:pos[i+1]] = in_raw_data[:,1][pos[i]]
                attributes[at][pos[-1]:] = in_raw_data[:,1][pos[-1]]
                
        at = '@' # special case: color change
        att_mask = in_raw_data[:,0]==at
        all_att_mask -= att_mask
        pos = np.nonzero(att_mask)[0] # locate the attributes changes
        if len(self.trailing_attributes):
            attributes[at][:pos[0]] = self.trailing_attributes[at][-1]
                
        if len(pos)>0:
            for i in range(len(pos)-1):
                attributes[at][pos[i]:pos[i+1]] = color_palette[in_raw_data[:,1][pos[i]].astype(np.int)]
            attributes[at][pos[-1]:] = color_palette[in_raw_data[:,1][pos[-1]].astype(np.int)]

        
        in_raw_data = in_raw_data[all_att_mask] # remove the lines defining color, size, layer, etc
        attributes = attributes[all_att_mask]
        if len(self.trailing_frame):
            in_raw_data = np.vstack((self.trailing_frame,in_raw_data))
            attributes = np.concatenate((self.trailing_attributes,attributes))

        # now split frames
        framebreaks = np.nonzero(in_raw_data[:,0]=='\n')[0]+1
        in_raw_data = np.split(in_raw_data, framebreaks)
        attributes = np.split(attributes, framebreaks)

        # and split according to object types
        obj_list = ['c','s','l','p','t']
        obj_vals = dict()
        obj_attrs = dict()

        

        if len(in_raw_data)>1:
            frange = range(len(in_raw_data)-1)
        else:
            frange = [0]

        for i in frange:
            
            frame = in_raw_data[i][:-1]
            attrs = attributes[i][:-1]
    
            obj_masks = {o: frame[:,0]==o for o in obj_list}
    
            o='c'
            if np.count_nonzero(obj_masks[o]):
                obj_vals[o] = np.reshape(np.genfromtxt(frame[:,1][obj_masks[o]], dtype='3f32'),(-1,3))
                obj_vals[o][:,2] = -obj_vals[o][:,2]
                obj_attrs[o] = attrs[obj_masks[o]]
    
            o='s'
            if np.count_nonzero(obj_masks[o]):
                obj_vals[o] = np.reshape(np.genfromtxt(frame[:,1][obj_masks[o]], dtype='6f32'),(-1,6))
                obj_vals[o][:,2] = -obj_vals[o][:,2]
                obj_vals[o][:,5] = -obj_vals[o][:,5]
                obj_attrs[o] = attrs[obj_masks[o]]

            
            o='l'
            if np.count_nonzero(obj_masks[o]):
                obj_vals[o] = np.reshape(np.genfromtxt(frame[:,1][obj_masks[o]], dtype='6f32'),(-1,6))
                obj_vals[o][:,2] = -obj_vals[o][:,2]
                obj_vals[o][:,5] = -obj_vals[o][:,5]
                obj_attrs[o] = attrs[obj_masks[o]]

            o='p'
            if np.count_nonzero(obj_masks[o]):
                split_vals = np.core.defchararray.partition(frame[:,1][obj_masks[o]], ' ')
                polygon_sizes = split_vals[:,0].astype(np.int)
                polygon_coords = split_vals[:,2]
                
                full_str = ''
                for str_a in polygon_coords:
                    full_str +=str_a
                    
                    obj_vals[o] = (polygon_sizes,np.reshape(np.fromstring(full_str, sep=' '),(-1,3)))
                    obj_vals[o][1][:,2] = -obj_vals[o][1][:,2]
                    obj_attrs[o] = attrs[obj_masks[o]]

            o='t'
            if np.count_nonzero(obj_masks[o]):
                split_vals = np.core.defchararray.partition(frame[:,1][obj_masks[o]], ' ')
                x = split_vals[:,0].astype(ftype)
                split_vals = np.core.defchararray.partition(split_vals[:,2], ' ')
                y = -split_vals[:,0].astype(ftype)
                split_vals = np.core.defchararray.partition(split_vals[:,2], ' ')
                z = split_vals[:,0].astype(ftype)
                text = split_vals[:,2]
                
                obj_vals[o] = (np.reshape(np.hstack((x,y,z)),(-1,3)), text)
                obj_attrs[o] = attrs[obj_masks[o]]


            self.frames.append(homerFrame.homerFrame(obj_vals, obj_attrs))

        if len(in_raw_data)>1:
            self.trailing_frame = in_raw_data[-1]
            self.trailing_attributes = attributes[-1]
        else:
            self.trailing_frame = []
            self.trailing_attributes = []
            
            
        self.is_init = False
        return True

