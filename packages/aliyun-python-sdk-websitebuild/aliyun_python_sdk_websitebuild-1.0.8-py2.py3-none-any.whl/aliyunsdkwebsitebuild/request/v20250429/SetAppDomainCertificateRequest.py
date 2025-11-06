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

class SetAppDomainCertificateRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'WebsiteBuild', '2025-04-29', 'SetAppDomainCertificate')
		self.set_protocol_type('https')
		self.set_method('POST')

	def get_DomainName(self): # String
		return self.get_query_params().get('DomainName')

	def set_DomainName(self, DomainName):  # String
		self.add_query_param('DomainName', DomainName)
	def get_PublicKey(self): # String
		return self.get_query_params().get('PublicKey')

	def set_PublicKey(self, PublicKey):  # String
		self.add_query_param('PublicKey', PublicKey)
	def get_CertificateType(self): # String
		return self.get_query_params().get('CertificateType')

	def set_CertificateType(self, CertificateType):  # String
		self.add_query_param('CertificateType', CertificateType)
	def get_PrivateKey(self): # String
		return self.get_query_params().get('PrivateKey')

	def set_PrivateKey(self, PrivateKey):  # String
		self.add_query_param('PrivateKey', PrivateKey)
	def get_BizId(self): # String
		return self.get_query_params().get('BizId')

	def set_BizId(self, BizId):  # String
		self.add_query_param('BizId', BizId)
	def get_CertificateName(self): # String
		return self.get_query_params().get('CertificateName')

	def set_CertificateName(self, CertificateName):  # String
		self.add_query_param('CertificateName', CertificateName)
