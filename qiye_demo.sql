-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- 主机： localhost
-- 生成日期： 2025-08-27 16:43:35
-- 服务器版本： 5.7.44-log
-- PHP 版本： 8.2.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 数据库： `qiyelist`
--

-- --------------------------------------------------------

--
-- 表的结构 `qiye_demo`
--

CREATE TABLE `qiye_demo` (
  `id` int(10) NOT NULL,
  `code` varchar(8) NOT NULL,
  `qy_name` varchar(80) DEFAULT NULL,
  `qy_status` varchar(20) DEFAULT NULL,
  `qy_fanren` varchar(330) DEFAULT NULL,
  `qy_ziben` varchar(30) DEFAULT NULL,
  `qy_date` varchar(30) DEFAULT NULL,
  `city` varchar(30) DEFAULT NULL,
  `quxian` varchar(30) DEFAULT NULL,
  `tel1` text,
  `tel2` text,
  `qy_email` varchar(50) DEFAULT NULL,
  `qy_shuihao` varchar(30) DEFAULT NULL,
  `qy_type` varchar(60) DEFAULT NULL,
  `qy_hangye` varchar(50) DEFAULT NULL,
  `qy_address` varchar(120) DEFAULT NULL,
  `qy_domain` varchar(50) DEFAULT NULL,
  `content` varchar(100) DEFAULT NULL,
  `flag` int(1) NOT NULL DEFAULT '0' COMMENT '是否已查'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘龙市企业名单';

--
-- 转储表的索引
--

--
-- 表的索引 `qiye_demo`
--
ALTER TABLE `qiye_demo`
  ADD PRIMARY KEY (`id`),
  ADD KEY `chk` (`qy_name`,`qy_domain`),
  ADD KEY `comp` (`flag`),
  ADD KEY `domain` (`qy_domain`) USING BTREE;

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `qiye_demo`
--
ALTER TABLE `qiye_demo`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
