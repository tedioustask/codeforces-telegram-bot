CREATE TABLE Problems
(
	Id SERIAL PRIMARY KEY,
	SiteId INTEGER,
	SiteIndex VARCHAR(10),
	UNIQUE(SiteId, SiteIndex),
	Name VARCHAR(200) NOT NULL,
	SolvedCount INTEGER, 
	Rating INTEGER,
	Tags TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE Contests
(
	Id SERIAL PRIMARY KEY,
	Tag VARCHAR(50),
	Rating INTEGER 
);

CREATE TABLE ContestInfo
(
	ContestId INTEGER REFERENCES Contests (Id),
	ProblemId INTEGER REFERENCES Problems (Id),
	UNIQUE(ContestId, ProblemId)
);



