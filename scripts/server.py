#!/usr/bin/env python

from reinforcement.srv import *
import rospy
from mazeGenerator import *
import sys
import argparse
import time
from action_server import RobotActionsServer 
import pickle
import copy


root_path = "/home/naman/catkin_ws/src/reinforcement/"
books = None
mazeInfo = None
mazeInfoCopy = None
parser = argparse.ArgumentParser()
parser.add_argument('-sub', help='for providing no. of subjects', metavar='5', action='store', dest='n_subjects', default=2, type=int)
parser.add_argument('-b', help='for providing no. of books for each subject', metavar='5', action='store', dest='n_books', default=2, type=int)
parser.add_argument('-s', help='for providing random seed', metavar='32', action='store', dest='seed', default=int(time.time()), type=int)
parser.add_argument('-action_seed', help='for providing action selection random seed', metavar='32', action='store', dest='action_seed', default=int(time.time()), type=int)
parser.add_argument('-headless', help='1 to run in the headless mode, 0 to launch gazebo', metavar='32', action='store', dest='headless', default=1, type=int)
robot_action_server = None


def check_is_edge(req):
	"""
	This function checks if two points are connected via edge or not.
	"""
	global mazeInfo
	# if valueFlag == "changedValuesLater":
	# 	if edge[2] < mazeInfo.grid_start or edge[2] > mazeInfo.grid_dimension*0.5 or edge[3] < mazeInfo.grid_start or edge[3] > mazeInfo.grid_dimension*0.5:
	# 		return False
	# elif valueFlag == "changedValuesBefore":
	# 	if edge[0] < mazeInfo.grid_start or edge[0] > mazeInfo.grid_dimension*0.5 or edge[1] < mazeInfo.grid_start or edge[1] > mazeInfo.grid_dimension*0.5:
	# 		return False
	edge = (req.x1,req.y1,req.x2,req.y2)
	for edge_point in edge:
		if edge_point < mazeInfo.grid_start or edge_point > mazeInfo.grid_dimension * 0.5:
			return 0
	print edge
	print edge in mazeInfo.blocked_edges
	print (edge[2],edge[3],edge[0],edge[1])
	print (edge[2],edge[3],edge[0],edge[1]) in mazeInfo.blocked_edges
	if edge in mazeInfo.blocked_edges or (edge[2],edge[3],edge[0],edge[1]) in mazeInfo.blocked_edges:
		return 0
	else:
		return 1

def is_terminal_state(req):
	if robot_action_server.current_state.count("placed") == len(books["books"].keys()):
		return 1
	else:
		return 0



def handle_get_current_state(req):
	"""
	This function will return initial state of turtlebot3.
	"""
	current_state = robot_action_server.current_state
	return current_state

def handle_reset_world(req):
	global mazeInfo
	mazeInfo = copy.deepcopy(mazeInfoCopy)
	robot_action_server.placed_books = []
	robot_action_server.current_state = robot_action_server.generate_init_state()
	return 1

def remove_blocked_edge(req):
	bookname = req.bookname
	global books
	global mazeInfo
	location_of_blocked_edge_list = books["books"][bookname]["load_loc"]
	if location_of_blocked_edge_list[0][0] <= location_of_blocked_edge_list[1][0] and location_of_blocked_edge_list[0][1] <= location_of_blocked_edge_list[1][1]:
		blocked_edge = (location_of_blocked_edge_list[0][0], location_of_blocked_edge_list[0][1], location_of_blocked_edge_list[1][0], location_of_blocked_edge_list[1][1])
	else:
		blocked_edge = (location_of_blocked_edge_list[1][0], location_of_blocked_edge_list[1][1], location_of_blocked_edge_list[0][0], location_of_blocked_edge_list[0][1])
	mazeInfo.blocked_edges.remove(blocked_edge)
	return "1"

def get_all_actions(req):
	global books
	actions = "(normal_moveF);(normal_TurnCW);(normal_TurnCCW);(careful_moveF);(careful_TurnCW);(careful_TurnCCW)"
	for i in books["books"]:
		actions+=";(normal_pick {});(careful_pick {})".format(i,i)
		for j in books["bins"]:
			actions+=";(normal_place {} {});(careful_place {} {})".format(i,j,i,j)
	return actions

def server():
	rospy.Service('get_all_actions',GetActions,get_all_actions)
	rospy.Service('get_current_state', GetInitialState, handle_get_current_state)
	rospy.Service('remove_blocked_edge', RemoveBlockedEdgeMsg,remove_blocked_edge)
	rospy.Service('check_is_edge',CheckEdge,check_is_edge)
	rospy.Service('is_terminal_state',IsTerminalState,is_terminal_state)
	rospy.Service('reset_world',ResetWorldMsg,handle_reset_world)
	print "Ready!"
	rospy.spin()
	
if __name__ == "__main__":
	global robot_action_server
	global mazeInfo
	global mazeInfoCopy
	args = parser.parse_args()
	n_subjects = args.n_subjects
	n_books = args.n_books
	seed = args.seed
	print n_subjects
	print n_books
	if n_subjects > 20:
		print('Maximum no. of subjects available is: 20')
		exit()
	book_sizes = 2
	book_count_of_each_subject = n_books * book_sizes
	book_count_list = [n_books] * n_subjects * book_sizes
	number_of_trollies = n_subjects * 2
	# grid_size = max((((book_count_of_each_subject * n_subjects) / 4) // 1 ) + 1, ((number_of_trollies/4)*7), 10)
	grid_size = 6 * n_subjects
	mazeInfo = Maze(grid_size, 0.5)
	books = mazeInfo.generate_blocked_edges(book_count_list, seed,  number_of_trollies, root_path)
	mazeInfoCopy = copy.deepcopy(mazeInfo)
	print mazeInfo.blocked_edges
	rospy.init_node('server')
	robot_action_server = RobotActionsServer(books,args.headless==1,args.action_seed)
	server()
