import pandas as pd
from sklearn.preprocessing import OneHotEncoder, LabelEncoder, OrdinalEncoder

def one_hot_encode_col(series):
    try:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    except TypeError:
        encoder = OneHotEncoder(sparse=False, handle_unknown="ignore")

    transformed = encoder.fit_transform(series.to_numpy().reshape(-1, 1))
    ohe_df = pd.DataFrame(
        transformed,
        columns=encoder.get_feature_names_out([series.name]),
        index=series.index
    )
    return ohe_df, encoder

def label_encode(series):
    encoder = LabelEncoder()
    return encoder.fit_transform(series), encoder

def ordinal_encode(X_train, X_val, X_test, categorical_cols, categories="auto"):
    encoder = OrdinalEncoder(categories=categories)
    return (encoder.fit_transform(X_train[categorical_cols]),
            encoder.transform(X_val[categorical_cols]),
            encoder.transform(X_test[categorical_cols]),
            encoder)
