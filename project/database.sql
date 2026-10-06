''' 
Yujin Lee created this file
- schema: maf (MakeArtsFund)
- table related UMF File
'''
create database maf;

use maf;

-- 
create table user (
	userId int,
    firstname varchar(50),
    surname varchar(50),
    email varchar(100),
    password varchar(100),
    accountStatus varchar(20),
    primary key (userId)
);


-- this table is child table of user.
-- make sure to inherit from user table. (add function related to inheritance)
create table artist (
	userId int,
    firstname varchar(50),
    surname varchar(50),
    email varchar(100),
    password varchar(100),
    accountStatus varchar(20),
    primary key (userId)

);