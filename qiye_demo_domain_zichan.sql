-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- 主机： localhost
-- 生成日期： 2025-08-27 16:43:43
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
-- 表的结构 `qiye_demo_domain_zichan`
--

CREATE TABLE `qiye_demo_domain_zichan` (
  `id` int(10) NOT NULL,
  `code` varchar(20) NOT NULL,
  `domain` varchar(40) NOT NULL,
  `ip` varchar(20) NOT NULL,
  `guishudi` varchar(120) NOT NULL,
  `http_status` varchar(30) NOT NULL,
  `https_status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业网络资产表';

--
-- 转储表的索引
--

--
-- 表的索引 `qiye_demo_domain_zichan`
--
ALTER TABLE `qiye_demo_domain_zichan`
  ADD PRIMARY KEY (`id`),
  ADD KEY `chk` (`code`,`ip`) USING BTREE;

--
-- 在导出的表使用AUTO_INCREMENT
--

--
-- 使用表AUTO_INCREMENT `qiye_demo_domain_zichan`
--
ALTER TABLE `qiye_demo_domain_zichan`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
