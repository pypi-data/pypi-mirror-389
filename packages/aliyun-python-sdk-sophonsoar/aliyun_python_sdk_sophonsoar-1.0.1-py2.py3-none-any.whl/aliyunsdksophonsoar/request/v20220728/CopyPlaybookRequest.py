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

class CopyPlaybookRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'sophonsoar', '2022-07-28', 'CopyPlaybook')
		self.set_protocol_type('https')
		self.set_method('POST')

	def get_SourcePlaybookUuid(self): # String
		return self.get_body_params().get('SourcePlaybookUuid')

	def set_SourcePlaybookUuid(self, SourcePlaybookUuid):  # String
		self.add_body_params('SourcePlaybookUuid', SourcePlaybookUuid)
	def get_RoleFor(self): # Long
		return self.get_query_params().get('RoleFor')

	def set_RoleFor(self, RoleFor):  # Long
		self.add_query_param('RoleFor', RoleFor)
	def get_Description(self): # String
		return self.get_body_params().get('Description')

	def set_Description(self, Description):  # String
		self.add_body_params('Description', Description)
	def get_ReleaseVersion(self): # String
		return self.get_body_params().get('ReleaseVersion')

	def set_ReleaseVersion(self, ReleaseVersion):  # String
		self.add_body_params('ReleaseVersion', ReleaseVersion)
	def get_DisplayName(self): # String
		return self.get_body_params().get('DisplayName')

	def set_DisplayName(self, DisplayName):  # String
		self.add_body_params('DisplayName', DisplayName)
	def get_RoleType(self): # String
		return self.get_query_params().get('RoleType')

	def set_RoleType(self, RoleType):  # String
		self.add_query_param('RoleType', RoleType)
	def get_Lang(self): # String
		return self.get_query_params().get('Lang')

	def set_Lang(self, Lang):  # String
		self.add_query_param('Lang', Lang)
