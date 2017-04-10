class OP(object):
	def __init__(self,name, link, description, skills,country,duration, salary):
		super(OP,self).__init__()
		self.link = link
		self.name = name
		self.description = description
		self.skills = skills
		self.country = country
		self.duration = duration
		self.salary = salary