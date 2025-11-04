# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from aliyunsdkcore.request import RpcRequest

class RunNotifyComponentWithMessageCenterRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'sophonsoar', '2022-07-28', 'RunNotifyComponentWithMessageCenter')
		self.set_protocol_type('https')
		self.set_method('POST')

	def get_EventId(self): # String
		return self.get_query_params().get('EventId')

	def set_EventId(self, EventId):  # String
		self.add_query_param('EventId', EventId)
	def get_RoleFor(self): # Long
		return self.get_query_params().get('RoleFor')

	def set_RoleFor(self, RoleFor):  # Long
		self.add_query_param('RoleFor', RoleFor)
	def get_ComponentName(self): # String
		return self.get_query_params().get('ComponentName')

	def set_ComponentName(self, ComponentName):  # String
		self.add_query_param('ComponentName', ComponentName)
	def get_Params(self): # String
		return self.get_query_params().get('Params')

	def set_Params(self, Params):  # String
		self.add_query_param('Params', Params)
	def get_ActionName(self): # String
		return self.get_query_params().get('ActionName')

	def set_ActionName(self, ActionName):  # String
		self.add_query_param('ActionName', ActionName)
	def get_NodeName(self): # String
		return self.get_query_params().get('NodeName')

	def set_NodeName(self, NodeName):  # String
		self.add_query_param('NodeName', NodeName)
	def get_PlaybookUuid(self): # String
		return self.get_query_params().get('PlaybookUuid')

	def set_PlaybookUuid(self, PlaybookUuid):  # String
		self.add_query_param('PlaybookUuid', PlaybookUuid)
	def get_AssetId(self): # Integer
		return self.get_query_params().get('AssetId')

	def set_AssetId(self, AssetId):  # Integer
		self.add_query_param('AssetId', AssetId)
	def get_RoleType(self): # String
		return self.get_query_params().get('RoleType')

	def set_RoleType(self, RoleType):  # String
		self.add_query_param('RoleType', RoleType)
	def get_Aliuid(self): # String
		return self.get_query_params().get('Aliuid')

	def set_Aliuid(self, Aliuid):  # String
		self.add_query_param('Aliuid', Aliuid)
	def get_Lang(self): # String
		return self.get_query_params().get('Lang')

	def set_Lang(self, Lang):  # String
		self.add_query_param('Lang', Lang)
	def get_ChannelTypeLists(self): # RepeatList
		return self.get_query_params().get('ChannelTypeList')

	def set_ChannelTypeLists(self, ChannelTypeList):  # RepeatList
		for depth1 in range(len(ChannelTypeList)):
			self.add_query_param('ChannelTypeList.' + str(depth1 + 1), ChannelTypeList[depth1])
