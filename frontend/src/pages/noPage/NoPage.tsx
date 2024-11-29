import React from 'react';
import styles from './NoPage.module.css';

const NoPage: React.FC = () => {
  return (
    <div className={styles.noPage}>
      <h1 className={styles.title}>404 - Page Not Found</h1>
      <p className={styles.message}>The page you're looking for doesn't exist.</p>
    </div>
  );
};

export default NoPage;
