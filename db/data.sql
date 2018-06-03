--
-- Dumping data for table `hosts`
--

INSERT INTO `hosts` (`id`, `host`, `host_user`, `path`, `updated_ts`) VALUES
(1, 'appliance', 'jharvard', 'logs/', '2015-05-09 07:07:56');

-- --------------------------------------------------------

--
-- Dumping data for table `patterns`
--

INSERT INTO `patterns` (`id`, `pattern`, `name`, `user`, `recipients`, `host`, `schedule_days`, `schedule_time`, `updated_ts`) VALUES
(17, 'error', 'Log Errors', 1, 'anonymous@gmail.com', 1, '56', '22:39:00', '2015-05-10 02:28:47'),
(18, 'error', 'Error', 1, 'anonymous@gmail.com', 1, '0123456', '22:30:00', '2015-05-10 02:35:29');

-- --------------------------------------------------------

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` (`id`, `role`) VALUES
(1, 'default');

-- --------------------------------------------------------

--
-- Dumping data for table `role_hosts`
--

INSERT INTO `role_hosts` (`role`, `host`, `updated_ts`) VALUES
(1, 1, '2015-05-09 07:07:56');
