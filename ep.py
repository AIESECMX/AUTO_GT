class EP(object):

	def __init__(self, name, email, lc,ep_id = 0, skills = None, ops = None,applicant = False,gr_id = 0, full_prifle =False):
		super(EP,self).__init__()
		self.name = name
		self.email = email
		self.lc = lc
		self.id = ep_id
		self.skills = skills
		self.ops = ops
		self.applicant = applicant	
		self.gr_id = gr_id
		self.full_prifle = full_prifle



		