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

class RunNotifyComponentWithWebhookRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'sophonsoar', '2022-07-28', 'RunNotifyComponentWithWebhook')
		self.set_protocol_type('https')
		self.set_method('POST')

	def get_RoleFor(self): # Long
		return self.get_query_params().get('RoleFor')

	def set_RoleFor(self, RoleFor):  # Long
		self.add_query_param('RoleFor', RoleFor)
	def get_Webhook(self): # String
		return self.get_query_params().get('Webhook')

	def set_Webhook(self, Webhook):  # String
		self.add_query_param('Webhook', Webhook)
	def get_ComponentName(self): # String
		return self.get_query_params().get('ComponentName')

	def set_ComponentName(self, ComponentName):  # String
		self.add_query_param('ComponentName', ComponentName)
	def get_Secret(self): # String
		return self.get_query_params().get('Secret')

	def set_Secret(self, Secret):  # String
		self.add_query_param('Secret', Secret)
	def get_ActionName(self): # String
		return self.get_query_params().get('ActionName')

	def set_ActionName(self, ActionName):  # String
		self.add_query_param('ActionName', ActionName)
	def get_Content(self): # String
		return self.get_query_params().get('Content')

	def set_Content(self, Content):  # String
		self.add_query_param('Content', Content)
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
	def get_Lang(self): # String
		return self.get_query_params().get('Lang')

	def set_Lang(self, Lang):  # String
		self.add_query_param('Lang', Lang)
	def get_MsgType(self): # String
		return self.get_query_params().get('MsgType')

	def set_MsgType(self, MsgType):  # String
		self.add_query_param('MsgType', MsgType)
